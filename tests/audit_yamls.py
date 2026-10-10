import glob
import yaml

print(f"{'EXPERIMENT ID':<35} | {'BIAS METHOD':<12} | {'DISTR':<10} | {'MERGE METHOD':<12} | {'MERGE INTERP':<14} | {'COVARS'}")
print("-" * 110)

for path in sorted(glob.glob("config/experiments_*/*.yaml")):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    exp_id = data.get("experiment_id", "")
    bias = data.get("bias_correction", {}) or {}
    merg = data.get("merging", {}) or {}
    interp = merg.get("interpolation", {}) or {}
    
    b_m = str(bias.get("method", "None"))
    b_d = str(bias.get("distribution") or bias.get("distr") or "-")
    m_m = str(merg.get("method", "None"))
    
    m_i = interp.get("method") or merg.get("interp_method")
    if not m_i and isinstance(merg.get("passes"), list) and len(merg["passes"]) > 0:
        p0 = merg["passes"][0]
        if isinstance(p0, dict):
            m_i = p0.get("interp_method")
    m_i = str(m_i or "None")
    
    cov = str(merg.get("covariables") or merg.get("auxiliary_variables") or "-")
    
    print(f"{exp_id:<35} | {b_m:<12} | {b_d:<10} | {m_m:<12} | {m_i:<14} | {cov}")
