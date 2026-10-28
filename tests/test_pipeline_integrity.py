"""Unit tests for CDT 8.0 Python orchestration pipeline integrity."""

import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
import yaml

from launcher.station_manager import (
    split_cdt_station_file,
    parse_cdt_station_file,
    read_holdout_station_ids,
)
from launcher.metrics import (
    compute_continuous_metrics,
    compute_categorical_metrics,
)
from launcher.cdt_bridge import CDTBridge, _to_r_val
from launcher.benchmark_reporter import (
    compute_leaderboard_ranking,
    generate_taylor_diagram,
    generate_radar_skill_chart,
    generate_metrics_heatmap,
    generate_roc_pod_vs_far,
    generate_interactive_html_dashboard,
)
from launcher.generate_pdf import generate_experiments_pdf


class TestStationManager(unittest.TestCase):
    """Test station splitting and validation metric calculations."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        # Create mock CDT station CSV (4 header rows: ID, LON, LAT, ELEV)
        self.mock_cdt_csv = self.temp_path / "mock_stations.csv"
        content = (
            "ID,STN01,STN02,STN03,STN04,STN05\n"
            "LON,-88.5,-87.2,-86.1,-85.4,-84.9\n"
            "LAT,13.5,14.2,15.1,12.8,11.9\n"
            "ELEV,120,450,890,230,15\n"
            "19910101,10.5,0.0,25.4,5.2,0.0\n"
            "19910102,0.0,12.1,0.0,0.0,8.4\n"
            "19910103,4.2,0.0,18.9,1.1,0.0\n"
        )
        self.mock_cdt_csv.write_text(content, encoding="utf-8")

        # Create holdout CSV (STN02, STN04)
        self.holdout_csv = self.temp_path / "holdout.csv"
        self.holdout_csv.write_text("station_id\nSTN02\nSTN04\n", encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_station_splitting(self):
        res = split_cdt_station_file(
            station_file=self.mock_cdt_csv,
            holdout_file=self.holdout_csv,
            output_dir=self.temp_path / "split_output",
        )
        self.assertEqual(len(res["holdout_ids"]), 2)
        self.assertIn("STN02", res["holdout_ids"])
        self.assertIn("STN04", res["holdout_ids"])
        self.assertEqual(res["training_count"], 3)
        self.assertEqual(res["holdout_count"], 2)
        self.assertTrue(Path(res["training_stations_file"]).exists())
        self.assertTrue(Path(res["holdout_stations_file"]).exists())

    def test_continuous_metrics(self):
        obs = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        sim_perfect = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        sim_shifted = np.array([12.0, 22.0, 32.0, 42.0, 52.0])

        m_perfect = compute_continuous_metrics(obs, sim_perfect)
        self.assertAlmostEqual(m_perfect["kge"], 1.0, places=4)
        self.assertAlmostEqual(m_perfect["r2"], 1.0, places=4)
        self.assertAlmostEqual(m_perfect["rmse"], 0.0, places=4)
        self.assertAlmostEqual(m_perfect["pbias"], 0.0, places=4)

        m_shifted = compute_continuous_metrics(obs, sim_shifted)
        self.assertLess(m_shifted["kge"], 1.0)
        self.assertGreater(m_shifted["kge"], 0.8)

    def test_categorical_scores(self):
        obs = np.array([0.0, 5.0, 10.0, 0.0, 15.0, 0.0])
        sim = np.array([0.0, 4.2, 8.5, 2.1, 14.0, 0.0])
        # Hits: 3 (idx 1, 2, 4), False Alarms: 1 (idx 3), Misses: 0, Correct Negatives: 2 (idx 0, 5)

        cat = compute_categorical_metrics(obs, sim, threshold=1.0)
        self.assertAlmostEqual(cat["pod"], 1.0, places=3)
        self.assertAlmostEqual(cat["far"], 0.25, places=3)  # 1 / (3 + 1)
        self.assertGreater(cat["ets"], 0.0)
        self.assertGreater(cat["hss"], 0.0)


class TestCDTBridge(unittest.TestCase):
    """Test dynamic R syntax conversion and CDTBridge setup."""

    def test_to_r_val_literals(self):
        self.assertEqual(_to_r_val(True), "TRUE")
        self.assertEqual(_to_r_val(False), "FALSE")
        self.assertEqual(_to_r_val(None), "NULL")
        self.assertEqual(_to_r_val(42), "42")
        self.assertEqual(_to_r_val(3.14), "3.14")
        self.assertEqual(_to_r_val("hello"), '"hello"')
        self.assertEqual(_to_r_val(["a", "b"]), 'c("a", "b")')
        self.assertEqual(_to_r_val({"key": "val"}), 'list(key = "val")')

    def test_cdt_bridge_init(self):
        bridge = CDTBridge()
        self.assertTrue(bridge.rscript_path.exists())
        self.assertIn("Rscript", str(bridge.rscript_path))

    def test_downscaling_methods_exist(self):
        bridge = CDTBridge()
        self.assertTrue(hasattr(bridge, "compute_downscaling_coefficients_temp"))
        self.assertTrue(hasattr(bridge, "downscale_temperature"))


class TestCheckpointAndResume(unittest.TestCase):
    """Test daily file coverage checking, resume date identification, and directory consolidation."""

    def test_check_daily_files_coverage_complete(self):
        from launcher.experiment_runner import check_daily_files_coverage, consolidate_daily_files
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            for d in ("19910101", "19910102", "19910103"):
                f = p / f"rr_adj_{d}.nc"
                f.write_bytes(b"x" * 2000)
            is_comp, res_dt, count, tot = check_daily_files_coverage(p, "rr_adj_", "19910101", "19910103")
            self.assertTrue(is_comp)
            self.assertIsNone(res_dt)
            self.assertEqual(count, 3)
            self.assertEqual(tot, 3)

    def test_check_daily_files_coverage_interrupted(self):
        from launcher.experiment_runner import check_daily_files_coverage
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            (p / "rr_mrg_19910101.nc").write_bytes(b"x" * 2000)
            corrupt = p / "rr_mrg_19910102.nc"
            corrupt.write_bytes(b"")
            is_comp, res_dt, count, tot = check_daily_files_coverage(p, "rr_mrg_", "19910101", "19910103")
            self.assertFalse(is_comp)
            self.assertEqual(res_dt, "19910102")
            self.assertEqual(count, 1)
            self.assertFalse(corrupt.exists())

    def test_consolidate_daily_files(self):
        from launcher.experiment_runner import consolidate_daily_files
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            sub1 = base / "DATA"
            sub2 = base / "MERGED_RAIN_19910102_19910103" / "DATA"
            sub1.mkdir(parents=True)
            sub2.mkdir(parents=True)
            (sub1 / "rr_mrg_19910101.nc").write_bytes(b"x" * 2000)
            (sub2 / "rr_mrg_19910102.nc").write_bytes(b"x" * 2000)
            primary = consolidate_daily_files(base, "rr_mrg_")
            self.assertEqual(primary, sub1)
            self.assertTrue((sub1 / "rr_mrg_19910101.nc").exists())
            self.assertTrue((sub1 / "rr_mrg_19910102.nc").exists())


class TestBenchmarkReporter(unittest.TestCase):
    """Test benchmark leaderboard ranking calculations."""

    def test_leaderboard_ranking(self):
        df_summaries = pd.DataFrame([
            {
                "experiment_id": "EXP_R01_Control",
                "variable": "rainfall",
                "kge": 0.55,
                "r": 0.60,
                "rmse": 6.8,
                "mae": 3.4,
                "pbias": 8.5,
                "pod": 0.72,
                "far": 0.35,
                "ets": 0.42,
                "hss": 0.50,
            },
            {
                "experiment_id": "EXP_R07_RK_DEM",
                "variable": "rainfall",
                "kge": 0.82,
                "r": 0.88,
                "rmse": 4.1,
                "mae": 2.1,
                "pbias": 1.2,
                "pod": 0.91,
                "far": 0.14,
                "ets": 0.73,
                "hss": 0.79,
            },
        ])
        df_ranked = compute_leaderboard_ranking(df_summaries)
        self.assertEqual(len(df_ranked), 2)
        self.assertEqual(df_ranked.iloc[0]["experiment_id"], "EXP_R07_RK_DEM")
        self.assertTrue(df_ranked.iloc[0]["is_winner"])

    def test_benchmark_figures_and_dashboard_generation(self):
        with tempfile.TemporaryDirectory() as td:
            temp_dir = Path(td)
            figures_dir = temp_dir / "figures"
            figures_rain = figures_dir / "rainfall"
            figures_rain.mkdir(parents=True, exist_ok=True)

            df_summaries = pd.DataFrame([
                {
                    "experiment_id": "EXP_R01_Control",
                    "variable": "rainfall",
                    "kge": 0.55,
                    "r": 0.60,
                    "rmse": 6.8,
                    "mae": 3.4,
                    "pbias": 8.5,
                    "pod": 0.72,
                    "far": 0.35,
                    "ets": 0.42,
                    "hss": 0.50,
                },
                {
                    "experiment_id": "EXP_R15_QM_RK_Coviables",
                    "variable": "rainfall",
                    "kge": 0.88,
                    "r": 0.91,
                    "rmse": 3.8,
                    "mae": 1.9,
                    "pbias": 0.8,
                    "pod": 0.94,
                    "far": 0.11,
                    "ets": 0.78,
                    "hss": 0.82,
                },
            ])
            df_ranked = compute_leaderboard_ranking(df_summaries)

            taylor_png = figures_rain / "fig_taylor.png"
            radar_png = figures_rain / "fig_radar.png"
            heatmap_png = figures_rain / "fig_heatmap.png"
            roc_png = figures_rain / "fig_roc.png"

            generate_taylor_diagram(df_ranked, taylor_png, var_type="rainfall")
            generate_radar_skill_chart(df_ranked, radar_png, var_type="rainfall")
            generate_metrics_heatmap(df_ranked, heatmap_png, var_type="rainfall")
            generate_roc_pod_vs_far(df_ranked, roc_png)

            self.assertTrue(taylor_png.exists() and taylor_png.stat().st_size > 0)
            self.assertTrue(radar_png.exists() and radar_png.stat().st_size > 0)
            self.assertTrue(heatmap_png.exists() and heatmap_png.stat().st_size > 0)
            self.assertTrue(roc_png.exists() and roc_png.stat().st_size > 0)

            # Test HTML dashboard generation
            fig_map = {
                "rainfall": {
                    "taylor": str(taylor_png),
                    "radar": str(radar_png),
                    "heatmap": str(heatmap_png),
                    "roc": str(roc_png),
                    "kge_boxplots": "",
                    "strata": "",
                }
            }
            html_out = temp_dir / "benchmark_report.html"
            generate_interactive_html_dashboard(df_ranked, fig_map, html_out)
            self.assertTrue(html_out.exists() and html_out.stat().st_size > 0)

            # Check that tabs, lightbox modal, and experiment IDs are inside the rendered HTML
            html_text = html_out.read_text(encoding="utf-8")
            self.assertIn("tab-btn-rainfall", html_text)
            self.assertIn("plot_taylor_rainfall", html_text)
            self.assertIn("EXP_R15_QM_RK_Coviables", html_text)
from launcher.data_preprocessor import validate_project_inputs, check_data_readiness


class TestDataValidator(unittest.TestCase):
    """Test dataset pre-flight validation and diagnostic reporting."""

    def test_validate_project_inputs(self):
        with tempfile.TemporaryDirectory() as td:
            temp_dir = Path(td)
            # Create a mock config dict
            cfg = {
                "paths": {
                    "stations_rainfall_file": str(temp_dir / "mock_precip.csv"),
                    "dem_file": str(temp_dir / "mock_dem.nc"),
                    "shapefile_path": str(temp_dir / "mock_shp.shp"),
                    "holdout_stations_file": str(temp_dir / "mock_holdout.csv"),
                    "satellite_rainfall_dir": str(temp_dir / "chirps_daily"),
                },
                "period": {
                    "start_date": "19910101",
                    "end_date": "19910103",
                }
            }
            res = validate_project_inputs(config_path_or_dict=cfg, verbose=False)
            self.assertIn("status", res)
            self.assertIn("errors", res)
            self.assertIn("details", res)
            # Since files don't exist in empty temp_dir, it should report missing files
            self.assertEqual(res["status"], "ERRORS")
            self.assertFalse(res["is_ready"])


class TestRegionalRouting(unittest.TestCase):
    """Test regional routing (ca vs rd) in ExperimentRunner and data_preprocessor."""

    def test_regional_experiment_normalization(self):
        from launcher.experiment_runner import ExperimentRunner
        
        # Test CA domain routing
        runner_ca = ExperimentRunner(
            config_target="config/experiments_rainfall/EXP_R01_SBA_IDW_Baseline.yaml",
            base_config_path="config/global_config.yaml",
            region="ca",
        )
        configs_ca = runner_ca.load_configs()
        self.assertEqual(len(configs_ca), 1)
        paths_ca = configs_ca[0]["paths"]
        self.assertIn("ca", paths_ca["stations_rainfall_file"])
        self.assertIn("experiments_ca", paths_ca["output_dir"])

        # Test RD domain routing
        runner_rd = ExperimentRunner(
            config_target="config/experiments_rainfall/EXP_R01_SBA_IDW_Baseline.yaml",
            base_config_path="config/global_config.yaml",
            region="rd",
        )
        configs_rd = runner_rd.load_configs()
        self.assertEqual(len(configs_rd), 1)
        paths_rd = configs_rd[0]["paths"]
        self.assertIn("rd", paths_rd["stations_rainfall_file"])
        self.assertIn("experiments_rd", paths_rd["output_dir"])

    def test_variable_specific_holdout_routing(self):
        from launcher.experiment_runner import ExperimentRunner
        
        # Rainfall experiment
        runner_rain = ExperimentRunner(
            config_target="config/experiments_rainfall/EXP_R01_SBA_IDW_Baseline.yaml",
            base_config_path="config/global_config.yaml",
            region="ca",
        )
        cfg_rain = runner_rain.load_configs()[0]
        # Temperature experiment
        runner_tmax = ExperimentRunner(
            config_target="config/experiments_tmax/EXP_TX01_SBA_IDW_Baseline.yaml",
            base_config_path="config/global_config.yaml",
            region="ca",
        )
        cfg_tmax = runner_tmax.load_configs()[0]
        
        # Verify that holdout files are differentiated
        self.assertIn("holdout_stations_file", cfg_rain["paths"])
        self.assertIn("holdout_stations_file", cfg_tmax["paths"])

    def test_temperature_variable_normalization(self):
        from launcher.experiment_runner import ExperimentRunner
        runner_tx = ExperimentRunner(
            config_target="config/experiments_tmax/EXP_TX01_SBA_IDW_Baseline.yaml",
            base_config_path="config/global_config.yaml",
            region="ca",
        )
        cfg_tx = runner_tx.load_configs()[0]
        # In CHIRTS NetCDFs and CDT temperature engine, the internal variable is 'temp'
        self.assertEqual(cfg_tx["paths"]["var_id"], "temp")
        self.assertIn("tmax", cfg_tx["paths"]["satellite_format"])

        runner_tn = ExperimentRunner(
            config_target="config/experiments_tmin/EXP_TN01_SBA_IDW_Baseline.yaml",
            base_config_path="config/global_config.yaml",
            region="ca",
        )
        cfg_tn = runner_tn.load_configs()[0]
        self.assertEqual(cfg_tn["paths"]["var_id"], "temp")
        self.assertIn("tmin", cfg_tn["paths"]["satellite_format"])


class TestParallelCores(unittest.TestCase):
    """Test automatic and explicit core configuration."""

    def test_cdt_bridge_cores(self):
        bridge_auto = CDTBridge(nb_cores="auto")
        self.assertEqual(bridge_auto.nb_cores, "auto")

        bridge_fixed = CDTBridge(nb_cores=8)
        self.assertEqual(bridge_fixed.nb_cores, 8)


class TestPDFGeneration(unittest.TestCase):
    """Test PDF compilation."""

    def test_generate_pdf(self):
        with tempfile.TemporaryDirectory() as td:
            pdf_path = Path(td) / "test_report.pdf"
            generated = generate_experiments_pdf(output_path=pdf_path)
            self.assertTrue(generated.exists())
            self.assertGreater(generated.stat().st_size, 5000)


class TestExperimentYAMLConsistency(unittest.TestCase):
    """Ensure all 26 experiment YAML configurations are strictly compliant with CDT 8.0."""

    def test_all_experiment_yamls_valid(self):
        import glob
        yaml_files = sorted(glob.glob("config/experiments_*/*.yaml"))
        self.assertIn(len(yaml_files), (26, 31), f"Expected 26 or 31 experiment YAMLs, found {len(yaml_files)}")

        valid_merge_methods = {"SBA", "RK"}
        valid_interp_methods = {"idw", "okr", "barnes", "cressman", "shepard", "sphere"}
        valid_bias_methods = {"mbvar", "mbmon", "qmdist", "qmecdf", "qm.ecdf"}
        valid_distrs = {"berngamma", "bernweibull", "bernlnorm", "norm", "snorm", "gumbel", "lnorm", "gamma"}

        for p in yaml_files:
            with self.subTest(yaml_file=p):
                with open(p, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f)

                # Check merging method
                merg = cfg.get("merging", {})
                self.assertIn(merg.get("method"), valid_merge_methods, f"Invalid merge method in {p}")

                # Check interpolation method
                interp = merg.get("interpolation", {})
                interp_m = interp.get("method") or merg.get("interp_method")
                if not interp_m and isinstance(merg.get("passes"), list) and len(merg["passes"]) > 0:
                    interp_m = merg["passes"][0].get("interp_method")
                self.assertIn(interp_m, valid_interp_methods, f"Invalid interpolation method '{interp_m}' in {p}")

                # Check bias correction method and distribution if configured
                bias = cfg.get("bias_correction", {})
                if bias and bias.get("method"):
                    b_method = str(bias.get("method")).lower()
                    self.assertIn(b_method, valid_bias_methods, f"Invalid bias method '{b_method}' in {p}")

                    distr = bias.get("distribution") or bias.get("distr")
                    if distr:
                        self.assertIn(str(distr).lower(), valid_distrs, f"Invalid distribution '{distr}' in {p}")

    def test_all_temperature_yamls_have_temp_var_id(self):
        import glob
        temp_yamls = sorted(glob.glob("config/experiments_tm*/*.yaml"))
        self.assertEqual(len(temp_yamls), 16)
        for p in temp_yamls:
            with self.subTest(yaml_file=p):
                with open(p, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f)
                self.assertEqual(cfg.get("var_id"), "temp", f"Expected var_id 'temp' for CHIRTS NetCDFs in {p}")


if __name__ == "__main__":
    unittest.main()

