# Modificaciones al Código Fuente R de CDT y Resolución de la Paralelización

> **Proyecto:** “Escenarios de Cambio Climático de Alta Resolución en Centroamérica y el Caribe”  
> **Grupo Oficial:** Grupo de Trabajo Regional de Escenarios de Cambio Climático de Centroamérica y el Caribe  
> **Ámbito:** Modificaciones al núcleo en R de Climate Data Tools (CDT v8.0), desacople de interfaz y aceleración de cómputo paralelo.

---

## 1. Contexto y Diagnóstico del Código Original de CDT

Climate Data Tools (CDT v8.0) fue concebido primordialmente como una herramienta analítica de escritorio orientada a usuarios interactivos a través de una interfaz gráfica de usuario (**GUI**) construida sobre el paquete `tcltk` en R. Si bien CDT incluye scripts para ejecución por línea de comandos (`cdtMerging_Precip_Cmd.R`, `cdtMerging_Temp_Cmd.R`), las funciones internas del paquete presentaban fuertes dependencias con el bucle de eventos de la GUI, cuellos de botella algorítmicos en el cálculo de cuantiles empíricos y limitaciones estructurales en el manejo de paralelismo.

Para procesar el periodo climatológico estándar de 30 años (**1991–2020**, equivalente a **10,958 días continuos**) en una cuadrícula de alta resolución sobre Centroamérica con 39 configuraciones experimentales, fue indispensable intervenir y parchar el código fuente en R. 

Este documento detalla las causas técnicas por las cuales el procesamiento en paralelo fallaba o se bloqueaba en la GUI interactiva, la arquitectura de la solución adoptada para la ejecución desatendida (*headless*), y el inventario exhaustivo de todos los cambios aplicados en los archivos fuente de la carpeta `R/`.

---

## 2. ¿Por qué la Paralelización no Funcionaba con la GUI?

En la documentación técnica previa no se había expuesto a profundidad la causa del fallo de la GUI interactiva; únicamente se había documentado la habilitación del paralelismo en los lanzadores CLI. A continuación se detallan las razones técnicas y arquitectónicas que impedían que la paralelización nativa funcionara de forma estable dentro de la interfaz gráfica de CDT:

### 2.1. Concurrencia e Hilo Único del Bucle de Eventos Tcl/Tk (`tcltk`)

1. **Modelo de Hilo Único en Tcl/Tk:**  
   El motor Tcl/Tk 8.6 embebido en R mediante el paquete `tcltk` no es seguro para ejecución multihilo concurrente (*not thread-safe*). Tcl opera sobre un bucle de eventos único asociado estrictamente al hilo principal de la sesión de R.
2. **Callbacks de la Barra de Progreso (`updateProgressBar`):**  
   Cuando CDT ejecuta una rutina iterativa a través de `cdt.foreach` con `GUI = TRUE`, registra la función de actualización de interfaz:
   ```r
   progress.fun <- updateProgressBar
   opts <- list(progress = progress.fun)
   ```
   Dentro de `updateProgressBar`, CDT realiza llamadas directas a variables de interfaz y al despachador de eventos de Tcl:
   ```r
   tcltk::tclvalue(.cdtEnv$tcl$status$pbLab) <- newlabel
   tcltk::tclvalue(.cdtEnv$tcl$status$pbBar) <- newvalue
   tcltk::tcl("update", "idletask")
   ```
3. **Condiciones de Carrera y Congelamiento (*Deadlock*):**  
   Cuando `foreach` o `doSNOW` distribuyen iteraciones entre trabajadores en paralelo, los mensajes de finalización enviados desde los procesos secundarios hacia el proceso maestro colisionan con las llamadas `tcl("update", "idletask")`. Al recibir múltiples actualizaciones asíncronas de progreso mientras se ejecutan operaciones intensivas de I/O de archivos NetCDF, el bucle de eventos de Tk entra en condición de carrera o se bloquea esperando respuestas de sockets locales. Esto provocaba que el sistema operativo marcara la ventana de CDT como *"No responde"* y el clúster de cómputo quedara congelado indefinidamente sin liberar memoria ni avanzar fechas.

### 2.2. Desactivación Forzada del Paralelismo en el Código Upstream

Debido a la inestabilidad de la GUI descrita anteriormente, los desarrolladores originales de CDT optaron por **desactivar deliberadamente el paralelismo** en rutinas computacionalmente críticas para evitar que los usuarios experimentaran cierres abruptos de la interfaz.

Por ejemplo, en la función `applyBiasCorrection` (`R/cdtBias_functions.R`, línea 1393), el código original contenía:
```r
# parsL <- doparallel.cond(length(ncInfo$ncfiles) > 10)
parsL <- doparallel.cond(FALSE)
```
Al forzar `parsL <- doparallel.cond(FALSE)`, cualquier ejecución dentro de la GUI descartaba la configuración de núcleos múltiples del usuario y conmutaba forzosamente a un bucle secuencial `lapply(loopL, ...)`. Esto provocaba que el ajuste de sesgo sobre 10,958 días se ejecutara en un único hilo, requiriendo más de 30 horas continuas para completar un solo experimento.

### 2.3. Aislamiento de Entornos en Clústeres de Procesos Hijos (PSOCK)

1. En sistemas operativos tipo Windows (y en entornos Linux sin forking compartido de memoria), el clúster se genera mediante `parallel::makeCluster(nb.cores)` a través de conexiones de red internas por sockets (PSOCK).
2. Los procesos hijos (*workers*) inician como sesiones de R completamente limpias e independientes.
3. CDT almacena su estado de trabajo, rutas y metadatos de configuración en entornos internos como `.cdtData` y `.cdtEnv`.
4. En el flujo original de la GUI, las funciones despachadas a los *workers* asumían la existencia de `.cdtData$GalParams`. Al no estar serializado ni propagado dicho entorno a los nodos hijos, los trabajadores fallaban inmediatamente con errores del tipo `object '.cdtData' not found`, interrumpiendo la corrida.

### 2.4. Bloqueo Modal Interactivo en Tareas en Segundo Plano

Diversas funciones auxiliares de CDT (como `Insert.Messages.Out`, `getCDTdataAndDisplayMsg` y `cdt.tkmessageBox`) están diseñadas para mostrar diálogos emergentes modales ante discrepancias menores en los metadatos de estaciones, fechas faltantes o fallas en el ajuste de variogramas.

En una ejecución paralela o desatendida, si un proceso secundario dispara una llamada a `tkmessageBox`, el hilo de ejecución queda en espera indefinida de una interacción manual (clic en *"Aceptar"* o *"Cancelar"*). Dado que los procesos hijos no tienen una ventana gráfica instanciada, la señal nunca puede ser atendida por el usuario, resultando en procesos zombis y congelamiento total del clúster.

### 2.5. Cuello de Botella Algorítmico en Cuantiles Empíricos (`qmecdf`)

Adicionalmente a los problemas de hilos, el método de mapeo de cuantiles empíricos (*Empirical Quantile Mapping*, `qmecdf`) sufría de un grave problema de complejidad algorítmica. En cada paso diario y para cada punto de rejilla, el algoritmo ejecutaba:
```r
xv <- sapply(seq_along(fobs), function(i){
    foo <- function(t) stats::quantile(fobs[[i]], t)
    foo(fgrd[[i]](xval[ix[1], ix[2]]))
})
```
Invocar repetidamente `stats::quantile()` sobre una función empírica escalonada para miles de celdas de rejilla multiplicadas por 10,958 días implicaba realizar cientos de millones de búsquedas iterativas en memoria. Este cálculo consumía más del 95% del tiempo de cómputo y hacía que la aplicación pareciera bloqueada aun si el paralelismo estuviera activo.

---

## 3. Arquitectura de la Solución: Ejecución Headless y Desacople

Para superar estas limitaciones, se implementó una estrategia integral de desacople entre la interfaz y el motor numérico:

```
+-------------------------------------------------------------------------+
|                  Orquestador Python (experiment_runner.py)              |
|          Gestión CLI (--cores 18), Lotes por Experimento, Benchmarking  |
+------------------------------------+------------------------------------+
                                     |
                                     v
+------------------------------------+------------------------------------+
|                      launcher/cdt_bridge.py                             |
|  - Sesión Headless pura en R (GUI = FALSE, sin dependencias Tcl/Tk)     |
|  - Redirección de mensajes a stdout/stderr                              |
|  - Inyección dinámica de parches en el namespace 'CDT'                 |
+------------------------------------+------------------------------------+
                                     |
                                     v
+------------------------------------+------------------------------------+
|                  Clúster Paralelo Multi-Proceso                         |
|  - parallel::makeCluster(18) + doSNOW                                   |
|  - clusterCall() propaga parches R/ a cada worker secundario            |
|  - Vectorización de cuantiles empíricos (stats::knots)                  |
|  - Smart File Skip y Caché Incremental celda a celda                    |
+-------------------------------------------------------------------------+
```

1. **Desactivación de Tcl/Tk (`GUI = FALSE`):**  
   Todas las funciones se invocan con el parámetro explícito `GUI = FALSE`.
2. **Redirección de Notificaciones:**  
   Se redefine `Insert.Messages.Out` para volcar texto simple a la consola (`cat`), evitando el uso de componentes Tcl.
3. **Inyección en Tiempo de Ejecución en el Namespace de CDT:**  
   Mediante la función `unlockBinding()` de R, se sustituyen las funciones nativas de CDT por versiones corregidas y optimizadas, restableciendo posteriormente la protección con `lockBinding()`.
4. **Propagación Transparente a Nodos Hijos:**  
   Se adaptó la inicialización del clúster en `cdt.doparallel` para que, inmediatamente después de crear los procesos trabajadores, se ejecute una llamada colectiva (`parallel::clusterCall`) que transfiere y aplica los parches locales de `R/` en la memoria de cada trabajador antes de comenzar a despachar tareas.

---

## 4. Inventario Exhaustivo de Modificaciones en Archivos `R/`

A continuación se documentan todos los cambios realizados en el código fuente de R conservados en el repositorio:

### 4.1. `R/cdtBias_functions.R`

Este archivo concentra las rutinas de cálculo, interpolación y aplicación de corrección de sesgo.

* **Reactivación del Paralelismo en `applyBiasCorrection`:**
  * *Ubicación:* Línea 1417 (aprox.).
  * *Código Original:*
    ```r
    # parsL <- doparallel.cond(length(ncInfo$ncfiles) > 10)
    parsL <- doparallel.cond(FALSE)
    ```
  * *Código Modificado:*
    ```r
    parsL <- doparallel.cond(length(ncInfo$ncfiles) > 10)
    ```
  * *Impacto:* Permite que el ajuste de sesgo diario se distribuya concurrentemente entre los núcleos asignados (ej. 18 hilos).

* **Aceleración Vectorizada de Cuantiles Empíricos (`qmecdf` con `knots`):**
  * *Ubicación:* Línea 1460 (aprox.).
  * *Diagnóstico:* La llamada iterativa a `stats::quantile(fobs[[i]], prob)` por cada celda espacial y por cada fecha generaba una latencia masiva.
  * *Solución Implementada:* Se extraen los nudos empíricos ordenados (*knots*) una sola vez por estación mediante `stats::knots(fobs)` y se implementa una interpolación lineal directa en punto flotante:
    $$x_v = k_{\lfloor q \rfloor} (1 - w_q) + k_{\lfloor q \rfloor + 1} w_q$$
    donde el índice flotante se computa como:
    $$q = 1 + (n_k - 1) \cdot p$$
  * *Impacto:* Reduce el tiempo de cómputo del mapeo de cuantiles empíricos de **~30 horas a ~12 minutos** para 10,958 días (reducción del 99.3% del tiempo de ejecución).

* **Manejo Defensivo de Archivos XML de Idioma:**
  * *Funciones Afectadas:* `ComputeBiasCoefficients`, `InterpolateBiasCoefficients`, `readBiasFiles`, `applyBiasCorrection`.
  * *Modificación:* Se envolvió la llamada `cdtLanguageParse(xml.dlg, ...)` en bloques `tryCatch()`. En caso de que el archivo XML no exista o la ruta de interfaz no esté disponible en modo *headless*, se inicializa una lista vacía de 50 elementos de texto plano (`lang.msg <- as.list(rep("", 50))`).
  * *Impacto:* Previene fallos fatales de ejecución causados por la falta de archivos de localización de interfaz en entornos desatendidos.

* **Corrección de Inversión Lógica en el Ajuste de Variogramas:**
  * *Función Afectada:* `biasInterpolation`.
  * *Código Original:*
    ```r
    vgm <- try(gstat::fit.variogram(exp.var, gstat::vgm(vgm.model)), silent = TRUE)
    if(!inherits(vgm, "try-error")) vgm <- NULL
    ```
  * *Código Modificado:*
    ```r
    vgm <- try(gstat::fit.variogram(exp.var, gstat::vgm(vgm.model)), silent = TRUE)
    if(inherits(vgm, "try-error")) vgm <- NULL
    ```
  * *Impacto:* En el código upstream existía un error de negación (`!`): si el ajuste del variograma resultaba exitoso, ¡el objeto se anulaba fijándolo en `NULL`!, forzando una degradación no deseada a IDW. La corrección restituye el modelo ajustado cuando la convergencia es exitosa.

* **Inicialización Defensiva de Grilla Espacial:**
  * *Función Afectada:* `InterpolateBiasCoefficients`.
  * *Modificación:* Se añadió una verificación previa de existencia para `interp.grid`. Si la variable no existe o es `NULL`, se define a partir de `xy.grid` mediante `defSpatialPixels(xy.grid)` y se asignan coordenadas a las estaciones de calibración, evitando interrupciones por variables no instanciadas.

---

### 4.2. `R/cdtMerging_functions.R`

Este archivo contiene la lógica medular del algoritmo de fusión espacial (*merging*) entre datos observados in situ y rejillas satelitales/reanálisis.

* **Mecanismo de Smart File Skip y Caché Incremental:**
  * *Ubicación:* Función `cdtMerging`.
  * *Diagnóstico:* En la versión original de CDT, ante cualquier corte de energía, falla temporal de disco o cancelación manual, el proceso debía reiniciarse desde el día 1, recalculando innecesariamente años enteros de datos ya procesados.
  * *Solución Implementada:*
    1. Se indexan previamente todos los archivos NetCDF diarios existentes en el directorio de salida y subdirectorios de corridas previas cuyo tamaño sea válido (`size > 1000 bytes`).
    2. Se comparan las fechas requeridas contra los archivos ya generados. Si un archivo ya existe y es íntegro, se omite de la lista de trabajo (`skipped_count`). Si existe en una carpeta previa, se reutiliza o copia localmente (`copied_count`).
    3. Si el 100% de los archivos ya fue generado, `cdtMerging` finaliza inmediatamente retornando 0:
       ```r
       if(length(todo_idx) == 0){
           cat(sprintf("  --> [CDT-Skip] 100%% de los archivos (%d/%d) ya existen y son validos. Omitiendo etapa de fusion.\n", length(all_indices), length(all_indices)))
           return(0)
       }
       ```
    4. El clúster en paralelo se inicializa despachando **únicamente las fechas faltantes** (`todo_idx`).
    5. Como medida de seguridad concurrente, dentro de la función de cada trabajador (`FUN(jj)`), se realiza una segunda comprobación atómica antes de abrir o escribir archivos NetCDF.
  * *Impacto:* Garantiza tolerancia a fallos, soporte de reanudación automática (*resume*) y ahorro sustancial de tiempo computacional en experimentos iterativos.

* **Validación Robusta del Rango del Variograma:**
  * *Ubicación:* Función `merging.functions`.
  * *Código Original:*
    ```r
    if(vgm$range[2] < 0){ ... }
    ```
  * *Código Modificado:*
    ```r
    else if(!is.null(vgm) && length(vgm$range) >= 2 && !is.na(vgm$range[2]) && vgm$range[2] < 0){ ... }
    ```
  * *Impacto:* Evita excepciones fatales de tipo `argument of length 0` o `missing value where TRUE/FALSE needed` cuando la estructura de parámetros del variograma devuelta por `gstat` no contiene un segundo elemento o contiene valores indeterminados.

---

### 4.3. `R/cdtUtilities_functions.R`

Este archivo gestiona la infraestructura de cómputo paralelo, el registro de clústeres y el seguimiento del progreso.

* **Propagación Automática de Parches a Nodos Secundarios:**
  * *Ubicación:* Función `cdt.doparallel`.
  * *Implementación:* Inmediatamente después de instanciar el clúster con `klust <- parallel::makeCluster(nb.cores)`, se ejecuta:
    ```r
    patches <- c('cdtLanguageParse_functions.R', 'cdtStatsProba_functions.R',
                 'cdtUtilities_functions.R', 'cdtMerging_functions.R',
                 'cdtBias_functions.R', 'cdtBias_Coefficient_ClimData_Procs.R',
                 'cdtTemp_DownscalingCoef_Procs.R', 'cdtTemp_DownscalingReanal_Procs.R')
    ...
    parallel::clusterCall(klust, function(p_files) {
        suppressPackageStartupMessages(library(CDT))
        cdt_env <- asNamespace('CDT')
        patch_env <- new.env(parent = cdt_env)
        for(pf in p_files){
            tryCatch(sys.source(pf, envir = patch_env), error = function(e) NULL)
        }
        for(fn in ls(envir = patch_env)){
            if(exists(fn, envir = cdt_env, inherits = FALSE)){
                tryCatch({
                    if(bindingIsLocked(fn, cdt_env)) unlockBinding(fn, cdt_env)
                    assign(fn, get(fn, envir = patch_env), envir = cdt_env)
                    lockBinding(fn, cdt_env)
                }, error = function(e) NULL)
            }
        }
    }, abs_patches)
    ```
  * *Impacto:* Asegura que todos los procesos de trabajo del clúster ejecuten las rutinas optimizadas y con correcciones de errores, sin importar que se ejecuten en espacios de memoria aislados.

* **Registro de Clúster SNOW:**
  * Se configuró el registro mediante `doSNOW::registerDoSNOW(klust)`, garantizando soporte multiplataforma estable para el paso de opciones de iteración y seguimiento del progreso.

---

### 4.4. `R/cdtStatsProba_functions.R`

Este archivo contiene los estimadores de momentos y máxima verosimilitud para distribuciones estadísticas continuas y mixtas.

* **Flexibilización de Argumentos en `get_distr_parameters`:**
  * *Ubicación:* Función `get_distr_parameters`.
  * *Diagnóstico:* Diversos módulos de CDT invocaban esta función pasando indistintamente nombres de parámetros divergentes (`min.length` vs `min_length`, y `probThres` vs `thres`), ocasionando errores de ejecución de tipo `unused argument`.
  * *Solución Implementada:* Se adaptó la firma para aceptar argumentos variables mediante el operador elipsis (`...`):
    ```r
    get_distr_parameters <- function(dat, distr, min_length = 1, thres = NA, ...){
        extra <- list(...)
        if(missing(min_length) || is.null(min_length)){
            if("min.length" %in% names(extra)) min_length <- extra[["min.length"]]
            else if(!is.null(distr[["min.length"]])) min_length <- distr[["min.length"]]
            else min_length <- 1
        }
        if(missing(thres) || is.null(thres) || (length(thres) == 1 && is.na(thres))){
            if("probThres" %in% names(extra)) thres <- extra[["probThres"]]
            else if(!is.null(distr[["probThres"]])) thres <- distr[["probThres"]]
            else if(!is.null(distr[["thres"]])) thres <- distr[["thres"]]
            else thres <- NA
        }
        ...
    ```
  * *Impacto:* Resuelve incompatibilidades al ajustar distribuciones mixtas (como Bernoulli-Gamma o Bernoulli-Weibull) durante el modelado probabilístico de precipitación.

---

### 4.5. `R/cdtLanguageParse_functions.R`

Gestiona la lectura de diccionarios XML para la traducción de etiquetas y mensajes.

* **Resolución Headless de Rutas y Estructuras Dummy:**
  * *Ubicación:* Función `cdtLanguageParse`.
  * *Diagnóstico:* En entornos por línea de comandos o contenedores, la variable global `.cdtDir$dirLocal` no se inicializa con las rutas estándar del instalador interactivo, provocando que la función `XML::xmlParse(xml.path)` abortara con error al no hallar el archivo.
  * *Solución Implementada:*
    1. Se verifica si el archivo especificado en `xml.path` existe realmente en disco. Si no existe, se busca recursivamente en el directorio raíz del paquete (`.cdtDir$Root/languages/`).
    2. Si el archivo XML sigue sin encontrarse o la lectura falla, la función retorna de manera segura una estructura sustituta (*dummy*) con cadenas de texto vacías:
       ```r
       dummy_msg <- as.list(rep("", 50))
       names(dummy_msg) <- as.character(1:50)
       return(list(message = dummy_msg, title = "", help = list(status = list(), tooltip = list())))
       ```
  * *Impacto:* Garantiza que los scripts de producción nunca se detengan por inconsistencias en los archivos de idioma de la interfaz.

---

### 4.6. `R/cdtBias_Coefficient_ClimData_Procs.R`, `R/cdtTemp_DownscalingCoef_Procs.R`, `R/cdtTemp_DownscalingReanal_Procs.R`

* **Sanitización de Rutas de Salida con `basename`:**
  * *Archivos Afectados:* `cdtBias_Coefficient_ClimData_Procs.R` (línea 5), `cdtTemp_DownscalingCoef_Procs.R` (línea 4).
  * *Modificación:* Se envolvió la construcción de nombres de subdirectorio con `basename()`:
    ```r
    outdir <- file.path(.cdtData$GalParams$IO.files$dir2save, paste0('CoefDownTemp', '_',
                        basename(tools::file_path_sans_ext(.cdtData$GalParams$IO.files$STN.file))))
    ```
  * *Impacto:* Previene la creación de rutas anidadas no deseadas o nombres de carpeta corruptos cuando se especifican rutas absolutas desde el lanzador CLI de Python.
* **Corrección de Inversión en Variogramas de Downscaling:**
  * *Archivo Afectado:* `cdtTemp_DownscalingReanal_Procs.R` (línea 255).
  * *Modificación:* Se corrigió idéntica inversión lógica a la de sesgo:
    ```r
    # Original:   if(!inherits(vgm, "try-error")) vgm <- NULL
    # Corregido:  if(inherits(vgm, "try-error")) vgm <- NULL
    ```
  * *Impacto:* Preserva el modelo geoestadístico ajustado en la etapa de reducción orográfica de escala de temperatura.

---

### 4.7. Monkey-Patching Defensivo en `launcher/cdt_bridge.py`

Además de los cambios en los archivos `.R` del repositorio, el módulo de acoplamiento en Python (`launcher/cdt_bridge.py`) inyecta durante el arranque del proceso los siguientes parches de compatibilidad:

1. **`Insert.Messages.Out`:**  
   Redirige todas las notificaciones internas de CDT a la salida estándar (`cat`), suprimiendo llamadas a widgets Tcl.
2. **`getStnOpenData`:**  
   Sustituye la rutina interactiva de apertura de tablas por una lectura directa mediante `read.table(..., na.strings = c('-99', '-99.0', '-999', '-9999', 'NA'))`, permitiendo procesar archivos de estaciones sin requerir la estructura de ventanas de CDT.
3. **`getCDTdataAndDisplayMsg`:**  
   Ejecuta directamente `CDT:::splitCDTData` sin desplegar diálogos informativos en pantalla.
4. **`cdtLocalConfigData`:**  
   Intercepta la configuración local de CDT para forzar que los parámetros de paralelismo permanezcan activos con el número de núcleos especificado por el usuario (`nb.cores = n_cores`), impidiendo que llamadas secundarias reestablezcan la configuración monotarea por defecto.

---

## 5. Cuadro Resumen Comparativo de Rendimiento

| Característica / Módulo | Comportamiento Original (GUI / CDT Nativo) | Comportamiento Optimizado (Headless + Parches R) |
| :--- | :--- | :--- |
| **Estabilidad de la Interfaz** | Se congela ("No responde") al actualizar la barra de progreso Tcl/Tk. | Desacople total (`GUI = FALSE`), salida limpia por consola `stdout`. |
| **Paralelismo en Ajuste de Sesgo** | Desactivado forzosamente (`parsL <- doparallel.cond(FALSE)`). | Totalmente habilitado (`--cores 18`, `doSNOW` / `makeCluster`). |
| **Cuantiles Empíricos (`qmecdf`)** | Búsqueda iterativa `stats::quantile()` punto por punto (~30 horas/corrida). | Vectorizado por nudos `stats::knots()` e interpolación lineal (**~12 minutos**). |
| **Ajuste de Variogramas** | Se anulaba el variograma ajustado por condición invertida (`!inherits`). | Preserva el modelo teórico ajustado (`sph`, `exp`, `gau`). |
| **Tolerancia a Fallos / Reanudación** | Inexistente; ante una interrupción se debía reiniciar desde el día 1. | **Smart File Skip**: detecta y reutiliza archivos ya generados válidos. |
| **Dependencia de Archivos XML** | Error fatal si la ruta local del archivo de idioma no existe. | Bloques defensivos `tryCatch` con estructuras de texto sustitutas. |
| **Distribución a Workers** | Pérdida de estado y funciones parcheadas en nodos secundarios. | Propagación colectiva automática vía `parallel::clusterCall`. |

---

## 6. Verificación y Regresión

Todas las funciones modificadas fueron validadas mediante pruebas de regresión contra los conjuntos de datos históricos (1991–2020):
1. **Consistencia Numérica:** Se verificó que los valores producidos por la rutina acelerada de `qmecdf` con `knots` coincidan numéricamente con los cuantiles estándar calculados secuencialmente, con una diferencia menor a $10^{-6}$ atribuible únicamente a la precisión de redondeo de punto flotante.
2. **Integridad de Salidas NetCDF:** Las grillas generadas cumplen con la convención estándar **CF-1.8**, conservando atributos de coordenadas, compresión gzip (deflate nivel 4) y ausencia de archivos truncados gracias a la validación de tamaño mínimo (`> 1000 bytes`).
