# Modificaciones al Código Fuente R de CDT y Resolución de la Paralelización

> **Proyecto:** “Escenarios de Cambio Climático de Alta Resolución en Centroamérica y el Caribe”  
> **Grupo Oficial:** Grupo de Trabajo Regional de Escenarios de Cambio Climático de Centroamérica y el Caribe  
> **Ámbito:** Modificaciones al núcleo en R de Climate Data Tools (CDT v8.0), desacople de interfaz y aceleración de cómputo paralelo.

---

## 1. Contexto y Diagnóstico del Código Original de CDT

Climate Data Tools (CDT v8.0) fue concebido primordialmente como una herramienta analítica de escritorio orientada a usuarios interactivos a través de una interfaz gráfica de usuario (**GUI**, por sus siglas en inglés, *Graphical User Interface*) construida sobre el paquete de ventanas `tcltk` en R. Si bien CDT incluye guiones para ejecución por línea de comandos (`cdtMerging_Precip_Cmd.R`, `cdtMerging_Temp_Cmd.R`), las funciones internas del paquete presentaban fuertes dependencias con el bucle de eventos visuales de la interfaz, cuellos de botella en el cálculo de cuantiles empíricos y limitaciones estructurales en el manejo de procesamiento concurrente.

Para procesar el periodo climatológico estándar de 30 años (**1991–2020**, equivalente a **10,958 días continuos**) en una cuadrícula de alta resolución sobre Centroamérica a través de 39 configuraciones experimentales, fue indispensable intervenir y ajustar el código fuente en R. 

Este documento detalla las razones técnicas por las cuales el procesamiento en paralelo fallaba o se bloqueaba dentro de la interfaz gráfica interactiva, la arquitectura de la solución adoptada para la ejecución sin entorno gráfico ni ventanas (modo desatendido o *headless*), y el inventario exhaustivo de todos los cambios aplicados en los archivos fuente de la carpeta `R/`.

---

## 2. ¿Por qué la Paralelización no Funcionaba con la Interfaz Gráfica (GUI)?

En la documentación técnica preliminar no se había profundizado en la causa raíz del fallo en la interfaz visual; únicamente se había documentado la habilitación del procesamiento multinúcleo en los scripts de terminal. A continuación se explican en lenguaje directo las razones que impedían la ejecución paralela estable dentro de la interfaz gráfica de CDT:

### 2.1. Concurrencia e Hilo Único del Bucle de Ventanas Tcl/Tk (`tcltk`)

1. **Modelo de un solo hilo de ejecución:**  
   El motor Tcl/Tk 8.6 utilizado por R para dibujar ventanas y botones no admite ejecución simultánea multihilo segura (propiedad conocida como *not thread-safe*). Tcl opera bajo un único canal o bucle de eventos asociado estrictamente al hilo principal de la sesión de R.
2. **Llamadas continuas de la barra de progreso (`updateProgressBar`):**  
   Cuando CDT ejecuta un cálculo repetitivo a través de la función `cdt.foreach` con la interfaz activa (`GUI = TRUE`), registra una función que redibuja la barra de avance:
   ```r
   progress.fun <- updateProgressBar
   opts <- list(progress = progress.fun)
   ```
   Dentro de `updateProgressBar`, CDT realiza llamadas directas a variables visuales y fuerza la actualización de la ventana:
   ```r
   tcltk::tclvalue(.cdtEnv$tcl$status$pbLab) <- newlabel
   tcltk::tclvalue(.cdtEnv$tcl$status$pbBar) <- newvalue
   tcltk::tcl("update", "idletask")
   ```
3. **Colisión de procesos y congelamiento mutuo (condición de carrera y *deadlock*):**  
   Cuando los paquetes de paralelismo (`foreach`, `doSNOW` o `parallel`) distribuyen días de cálculo entre múltiples núcleos del procesador, cada núcleo secundario envía avisos al proceso principal para indicar que terminó una tarea. Esos avisos colisionan con la instrucción `tcl("update", "idletask")`. Al saturarse el canal con cientos de peticiones de dibujo simultáneas mientras se leen y escriben archivos pesados NetCDF, el sistema entra en una condición de carrera (*race condition*) o bloqueo mutuo (*deadlock*). En este estado, la interfaz gráfica deja de responder ante el sistema operativo (mostrando el mensaje *"No responde"*) y el clúster de cómputo queda congelado indefinidamente sin avanzar en las fechas.

### 2.2. Desactivación Forzada en el Código Original de los Desarrolladores (*Hardcoded*)

Para evitar que la aplicación interactiva colapsara por los bloqueos visuales descritos, los programadores originales de CDT optaron por **desactivar deliberadamente el paralelismo** dentro de funciones numéricas intensivas, dejándolo fijado de manera rígida en el código fuente (práctica conocida técnicamente como *hardcoding*).

Por ejemplo, en la función de corrección de sesgo `applyBiasCorrection` (`R/cdtBias_functions.R`, línea 1393), el código original establecía textualmente:
```r
# parsL <- doparallel.cond(length(ncInfo$ncfiles) > 10)
parsL <- doparallel.cond(FALSE)
```
Al obligar la condición `parsL <- doparallel.cond(FALSE)`, cualquier orden dada desde la interfaz gráfica para utilizar múltiples núcleos de procesamiento era ignorada por completo, forzando un recorrido estrictamente secuencial de un día a la vez (`lapply`). Debido a esto, el procesamiento de los 10,958 días se realizaba en un solo núcleo, requiriendo más de 30 horas continuas para finalizar un único experimento.

### 2.3. Aislamiento de Memoria en Procesos Secundarios de Trabajo (*Workers*)

1. En sistemas operativos como Windows (y en servidores donde no se comparte la memoria del proceso padre), la creación de procesos en paralelo se realiza mediante conexiones de red internas por sockets (modo conocido como clúster PSOCK).
2. Cada proceso secundario de trabajo (habitualmente llamado *worker*) nace como una sesión limpia de R, completamente vacía e independiente.
3. CDT almacena sus rutas de trabajo, parámetros seleccionados y opciones en variables de sesión internas (`.cdtData` y `.cdtEnv`).
4. En el flujo original de la interfaz gráfica, las funciones enviadas a los procesos secundarios asumían que esas variables ya existían en memoria. Al no ser transferidas de forma explícita a cada proceso hijo, estos abortaban de inmediato con el mensaje de error `object '.cdtData' not found`, interrumpiendo la ejecución global.

### 2.4. Bloqueo por Ventanas Emergentes en Procesos en Segundo Plano

Diversas funciones auxiliares de CDT (como `Insert.Messages.Out`, `getCDTdataAndDisplayMsg` y `cdt.tkmessageBox`) fueron diseñadas para detener el programa y abrir una pequeña ventana de diálogo cada vez que ocurre una discrepancia menor, un dato faltante o una falla en el ajuste de un semivariograma.

Cuando estas funciones se ejecutan en segundo plano o dentro de un proceso secundario que carece de interfaz visual, la llamada intenta abrir una ventana inexistente y queda en **pausa indefinida** esperando que un usuario presione físicamente el botón *"Aceptar"*. Como nadie puede ver la ventana, el proceso queda suspendido de manera permanente (proceso huérfano o zombi) y detiene el resto de la cola de cómputo.

### 2.5. Ineficiencia en el Algoritmo de Cuantiles Empíricos (`qmecdf`)

Adicionalmente a los problemas de concurrencia, el algoritmo de mapeo de cuantiles empíricos (*Empirical Quantile Mapping*, `qmecdf`) presentaba una ineficiencia en su diseño matemático. En cada día y para cada celda de la rejilla, el código original realizaba una búsqueda iterativa punto por punto:
```r
xv <- sapply(seq_along(fobs), function(i){
    foo <- function(t) stats::quantile(fobs[[i]], t)
    foo(fgrd[[i]](xval[ix[1], ix[2]]))
})
```
Calcular `stats::quantile()` de forma repetitiva para decenas de miles de celdas espaciales a lo largo de 10,958 días implicaba cientos de millones de búsquedas secuenciales en memoria. Esta sola operación consumía más del 95% del tiempo de cálculo total, provocando que la aplicación pareciera paralizada aun si el procesamiento multinúcleo hubiese estado activo.

---

## 3. Arquitectura de la Solución: Ejecución Desatendida (*Headless*) y Desacople

Para solucionar estos inconvenientes de forma definitiva, se diseñó un desacople total entre el motor numérico de CDT y los componentes visuales:

```
+-------------------------------------------------------------------------+
|                  Orquestador en Python (experiment_runner.py)           |
|  Gestión por terminal (--cores 18), Lotes por Experimento y Validación  |
+------------------------------------+------------------------------------+
                                     |
                                     v
+------------------------------------+------------------------------------+
|                      launcher/cdt_bridge.py                             |
|  - Sesión desatendida pura en R (sin ventanas, GUI = FALSE)             |
|  - Salida limpia de mensajes por consola estándar (stdout/stderr)       |
|  - Carga e inyección dinámica de funciones corregidas en memoria        |
+------------------------------------+------------------------------------+
                                     |
                                     v
+------------------------------------+------------------------------------+
|                  Clúster Paralelo Multi-Proceso                         |
|  - parallel::makeCluster(18) + doSNOW                                   |
|  - Transferencia colectiva de funciones corregidas a cada proceso hijo  |
|  - Aceleración matemática de cuantiles empíricos (stats::knots)         |
|  - Detección inteligente de archivos ya calculados (smart file skip)    |
+-------------------------------------------------------------------------+
```

1. **Desactivación completa de componentes visuales (`GUI = FALSE`):**  
   Todas las llamadas internas a CDT se configuran con la bandera `GUI = FALSE`, suprimiendo cualquier intento de interactuar con ventanas o barras de progreso gráficas.
2. **Redirección de mensajes a la terminal:**  
   Se reprogramó la función de mensajes (`Insert.Messages.Out`) para que imprima texto directamente en la consola (`cat`), evitando el uso de ventanas emergentes.
3. **Sustitución de funciones en memoria durante la ejecución:**  
   Aprovechando el mecanismo de desbloqueo de variables de R (`unlockBinding`), se reemplazan en tiempo real las funciones originales de CDT por las versiones optimizadas y corregidas, protegiéndolas nuevamente con `lockBinding`.
4. **Propagación colectiva a todos los núcleos:**  
   Se modificó la rutina de inicialización del clúster (`cdt.doparallel`) para que, una vez creados los procesos secundarios en paralelo, se realice un envío masivo (`parallel::clusterCall`) que transfiere y activa el código corregido de la carpeta `R/` en la memoria de cada núcleo de trabajo.

---

## 4. Inventario Exhaustivo de Modificaciones en Archivos `R/`

A continuación se detalla cada una de las intervenciones realizadas en los códigos fuente en R:

### 4.1. `R/cdtBias_functions.R`

Este archivo concentra las rutinas de cálculo, interpolación y aplicación de corrección de sesgo.

* **Reactivación del procesamiento en paralelo en `applyBiasCorrection`:**
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
  * *Efecto práctico:* Permite que el cálculo del sesgo se distribuya de manera concurrente entre los 18 hilos del procesador.

* **Aceleración matemática de cuantiles empíricos mediante nudos ordenados (`knots`):**
  * *Ubicación:* Línea 1460 (aprox.).
  * *Diagnóstico:* La llamada iterativa a `stats::quantile()` por cada celda espacial y por cada fecha generaba una latencia inmanejable.
  * *Solución implementada:* Se extraen los puntos ordenados de quiebre o nudos (*knots*) una sola vez por cada estación mediante `stats::knots(fobs)` y se aplica una interpolación lineal directa en punto flotante:
    $$x_v = k_{\lfloor q \rfloor} (1 - w_q) + k_{\lfloor q \rfloor + 1} w_q$$
    donde la posición fraccionaria en el arreglo se obtiene como:
    $$q = 1 + (n_k - 1) \cdot p$$
  * *Efecto práctico:* El tiempo de cálculo para los 30 años (10,958 días) se redujo drásticamente de **~30 horas a solo ~12 minutos** (una reducción del 99.3% del tiempo de cómputo).

* **Protección ante ausencia de archivos de idioma XML:**
  * *Funciones Afectadas:* `ComputeBiasCoefficients`, `InterpolateBiasCoefficients`, `readBiasFiles`, `applyBiasCorrection`.
  * *Modificación:* Se envolvió la lectura del archivo de idioma `cdtLanguageParse()` en bloques de captura de errores (`tryCatch`). Si el archivo XML no existe en la ruta esperada de la interfaz, se crea automáticamente una lista vacía de texto (`lang.msg <- as.list(rep("", 50))`).
  * *Efecto práctico:* Evita que el cálculo se interrumpa abruptamente si faltan archivos auxiliares de traducción en servidores o contenedores.

* **Corrección del error lógico en el ajuste de semivariogramas:**
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
  * *Efecto práctico:* El código original tenía un signo de negación erróneo (`!`): cuando el semivariograma ajustaba con éxito, ¡lo convertía en `NULL` y descartaba el cálculo geoestadístico! La corrección restituye el modelo ajustado cuando la convergencia es exitosa.

* **Inicialización de seguridad para la cuadrícula espacial:**
  * *Función Afectada:* `InterpolateBiasCoefficients`.
  * *Modificación:* Se añadió una comprobación previa para verificar si `interp.grid` fue instanciada. Si se encuentra vacía o indefinida, se inicializa automáticamente a partir de `xy.grid` con la función `defSpatialPixels()` y se asignan coordenadas a las estaciones, previniendo errores por variables no inicializadas.

---

### 4.2. `R/cdtMerging_functions.R`

Este archivo contiene el algoritmo central de fusión espacial (*merging*) entre observaciones de estaciones in situ y campos satelitales o de reanálisis.

* **Omisión inteligente de archivos ya calculados y memoria intermedia (*smart file skip* y caché incremental):**
  * *Ubicación:* Función `cdtMerging`.
  * *Diagnóstico:* En la versión original de CDT, si una corrida de 30 años se interrumpía por corte eléctrico o reinicio en el día 10,000, el sistema obligaba a recalcular todo desde el día 1, perdiendo días de trabajo previo.
  * *Solución implementada:*
    1. Antes de iniciar la distribución paralela, el sistema inspecciona la carpeta de destino y subcarpetas para identificar archivos NetCDF diarios válidos ya generados (`size > 1000 bytes`).
    2. Compara el listado total de fechas requeridas contra los archivos válidos existentes. Si un archivo ya existe y es íntegro, lo omite de la lista de tareas; si está en una carpeta previa, lo copia y reutiliza.
    3. Si el 100% de los archivos ya se encuentra generado, la función finaliza de inmediato retornando 0:
       ```r
       if(length(todo_idx) == 0){
           cat(sprintf("  --> [CDT-Skip] 100%% de los archivos (%d/%d) ya existen y son validos. Omitiendo etapa de fusion.\n", length(all_indices), length(all_indices)))
           return(0)
       }
       ```
    4. El clúster concurrente se activa únicamente para procesar las **fechas faltantes** (`todo_idx`).
    5. Cada proceso de trabajo realiza una segunda verificación atómica antes de escribir en disco, evitando conflictos de escritura simultánea entre núcleos.
  * *Efecto práctico:* Proporciona soporte de reanudación automática de corridas (*resume*) y ahorra tiempo computacional ante ejecuciones repetitivas.

* **Validación de seguridad del rango del semivariograma:**
  * *Ubicación:* Función `merging.functions`.
  * *Código Original:*
    ```r
    if(vgm$range[2] < 0){ ... }
    ```
  * *Código Modificado:*
    ```r
    else if(!is.null(vgm) && length(vgm$range) >= 2 && !is.na(vgm$range[2]) && vgm$range[2] < 0){ ... }
    ```
  * *Efecto práctico:* Evita fallos fatales de tipo `argument of length 0` cuando el modelo devuelto por la librería `gstat` contiene valores indefinidos en sus parámetros de alcance o rango.

---

### 4.3. `R/cdtUtilities_functions.R`

Gestiona la infraestructura de cómputo paralelo y la creación de clústeres de procesos.

* **Transferencia de funciones corregidas a los procesos de trabajo (*workers*):**
  * *Ubicación:* Función `cdt.doparallel`.
  * *Implementación:* Justo después de crear el clúster (`klust <- parallel::makeCluster(nb.cores)`), se ejecuta una llamada colectiva `clusterCall()` que lee los archivos modificados de la carpeta `R/` y los inyecta en el entorno de cada proceso secundario.
  * *Efecto práctico:* Asegura que todos los núcleos secundarios ejecuten las versiones optimizadas y corregidas, aun cuando operen en espacios de memoria independientes.

* **Integración con el controlador `doSNOW`:**
  * Se configuró el registro formal mediante `doSNOW::registerDoSNOW(klust)`, garantizando una comunicación fluida entre el despachador de tareas y los procesos secundarios en plataformas Windows y Linux.

---

### 4.4. `R/cdtStatsProba_functions.R`

Contiene las funciones estadísticas para ajustar distribuciones de probabilidad teóricas a las observaciones.

* **Flexibilización de argumentos en `get_distr_parameters`:**
  * *Ubicación:* Función `get_distr_parameters`.
  * *Diagnóstico:* Distintos módulos de CDT llamaban a esta función usando indistintamente nombres de variables alternativos (como `min.length` frente a `min_length`, o `probThres` frente a `thres`), lo que provocaba errores de argumento desconocido (*unused argument*).
  * *Solución implementada:* Se añadió el operador de argumentos variables (`...`), permitiendo que la función reconozca automáticamente cualquiera de las variantes de nombre sin interrumpir el flujo.
  * *Efecto práctico:* Estabilidad total al ajustar distribuciones mixtas (como Bernoulli-Gamma o Bernoulli-Weibull) durante la corrección de precipitación.

---

### 4.5. `R/cdtLanguageParse_functions.R`

Gestiona la lectura de diccionarios XML de textos y etiquetas.

* **Búsqueda alternativa y estructuras seguras de reemplazo (*dummies*):**
  * *Ubicación:* Función `cdtLanguageParse`.
  * *Diagnóstico:* En ejecuciones sin interfaz gráfica, la variable de ruta local `.cdtDir$dirLocal` no se define, lo que causaba que `XML::xmlParse` arrojara un error fatal al no encontrar el archivo de idioma.
  * *Solución implementada:* Si el archivo no existe en la ruta indicada, se busca en la carpeta de instalación principal del paquete. Si continúa sin encontrarse, la función devuelve de manera segura una estructura sustituta con cadenas vacías, evitando que el programa se detenga por un mensaje de texto.

---

### 4.6. `R/cdtBias_Coefficient_ClimData_Procs.R` y Funciones de Reducción Orográfica (*Downscaling*)

* **Normalización de nombres de carpetas con `basename`:**
  * *Archivos Afectados:* `cdtBias_Coefficient_ClimData_Procs.R` (línea 5), `cdtTemp_DownscalingCoef_Procs.R` (línea 4).
  * *Modificación:* Se utilizó la función `basename()` para aislar únicamente el nombre del archivo de estaciones, evitando que rutas absolutas largas generen carpetas anidadas no deseadas en el disco duro.
* **Corrección de semivariogramas en desescalado de temperatura:**
  * *Archivo Afectado:* `cdtTemp_DownscalingReanal_Procs.R` (línea 255).
  * *Modificación:* Se corrigió idéntica condición invertida (`!inherits`) en la etapa de reducción orográfica de escala de temperatura diurna y nocturna.

---

### 4.7. Sustitución Dinámica de Funciones en Memoria (Técnica de *Monkey-Patching*) en `launcher/cdt_bridge.py`

La técnica de **sustitución dinámica de funciones en memoria** (conocida en ingeniería de software con el término en inglés *monkey-patching*) consiste en reemplazar o interceptar temporalmente una función interna de un programa mientras este se encuentra en ejecución, sin necesidad de alterar permanentemente el paquete instalado en el sistema operativo.

El puente en Python (`launcher/cdt_bridge.py`) aplica esta técnica al iniciar la sesión de R para redirigir las siguientes funciones interactivas:

1. **`Insert.Messages.Out`:**  
   Se sustituye para que vuelque los mensajes informativos directamente a la consola de texto estándar (`cat`), eliminando cualquier intento de crear componentes visuales de Tcl/Tk.
2. **`getStnOpenData`:**  
   Se reemplaza la rutina interactiva de selección de archivos por una lectura tabular directa mediante `read.table()`, permitiendo cargar las estaciones meteorológicas sin requerir la ventana del explorador de archivos.
3. **`getCDTdataAndDisplayMsg`:**  
   Se sustituye para que llame directamente al particionador de datos (`CDT:::splitCDTData`) sin mostrar avisos de confirmación en pantalla.
4. **`cdtLocalConfigData`:**  
   Se intercepta esta función para garantizar que la cantidad de núcleos asignados por el usuario (`nb.cores = n_cores`) se mantenga fija en memoria y no sea reescrita por la configuración monotarea por defecto de CDT.

---

## 5. Cuadro Resumen Comparativo de Rendimiento

| Característica / Módulo | Comportamiento Original (Interfaz Gráfica / CDT Nativo) | Comportamiento Optimizado (Modo Desatendido + Ajustes en R) |
| :--- | :--- | :--- |
| **Estabilidad operativa** | Se congela ("No responde") al intentar actualizar la barra gráfica de avance. | Desacople total (`GUI = FALSE`), salida limpia y directa por consola de texto. |
| **Paralelismo en corrección de sesgo** | Desactivado de forma rígida en el código (`parsL <- doparallel.cond(FALSE)`). | Totalmente habilitado y distribuido en 18 núcleos concurrentes (`--cores 18`). |
| **Cuantiles empíricos (`qmecdf`)** | Búsqueda iterativa punto por punto (~30 horas por corrida experimental). | Aceleración matemática por nudos ordenados e interpolación lineal (**~12 minutos**). |
| **Ajuste de semivariogramas** | Se anulaba el semivariograma ajustado por condición invertida (`!inherits`). | Preserva el modelo teórico ajustado (`sph`, `exp`, `gau`) para el cálculo de residuales. |
| **Tolerancia a fallos y reanudación** | Inexistente; ante una interrupción obligaba a reiniciar todo desde el día 1. | **Omisión inteligente (*smart file skip*)**: detecta y reutiliza archivos ya generados. |
| **Dependencia de archivos XML** | Error fatal si la ruta local del archivo de idioma no existe. | Captura de errores (`tryCatch`) con estructuras de sustitución seguras. |
| **Distribución a núcleos secundarios** | Pérdida de variables y funciones corregidas en procesos independientes. | Transferencia colectiva automática a cada núcleo vía `parallel::clusterCall`. |

---

## 6. Verificación de Consistencia Numérica

Todas las funciones modificadas fueron validadas mediante pruebas comparativas contra la serie histórica (1991–2020):
1. **Consistencia Numérica:** Se comprobó que los valores producidos por la rutina acelerada de `qmecdf` con nudos ordenados coinciden de forma exacta con los cuantiles calculados secuencialmente, presentando diferencias menores a $10^{-6}$ atribuibles únicamente a la precisión de redondeo de punto flotante de la máquina.
2. **Integridad de Salidas NetCDF:** Las cuadrículas generadas cumplen estrictamente con la convención climática estándar **CF-1.8**, conservando atributos de coordenadas, compresión sin pérdida (nivel 4) y ausencia de archivos incompletos gracias a la validación de tamaño mínimo (`> 1000 bytes`).
