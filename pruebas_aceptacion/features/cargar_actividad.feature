# language: es
# ID: CU-03  Nombre: Cargar actividades

Característica: CU-03 Cargar actividades
  Como alumno registrado en el sistema
  Quiero cargar evidencias en formato PDF de mis actividades
  Para que queden registradas en mi seminario

  Antecedentes:
    Dado que el alumno "amerinaga" con contraseña "amer1234" ha iniciado sesión
    Y el alumno navega al seminario 4

  @limpiar_evidencias
  Escenario: Carga exitosa de una actividad
    Cuando el alumno escribe "Reporte de avance" en el campo nombre
    Y el alumno adjunta el archivo "reporte.pdf"
    Y el alumno hace clic en el botón "Cargar actividad"
    Entonces la página muestra el texto "Evidencia subida correctamente."
    Y la página muestra el texto "Reporte de avance"

  Escenario: El botón está deshabilitado si el formulario está incompleto
    Entonces el botón con id "ev-submit" está deshabilitado
    Cuando el alumno escribe "Mi actividad" en el campo nombre
    Entonces el botón con id "ev-submit" está deshabilitado
    Cuando el alumno adjunta el archivo "actividad.pdf"
    Entonces el botón con id "ev-submit" está habilitado

  Escenario: FA-01 - El alumno sube un archivo que no es PDF
    Cuando el alumno escribe "Actividad incorrecta" en el campo nombre
    Y el alumno adjunta el archivo "imagen.jpg"
    Entonces la página muestra el texto "El archivo debe ser un PDF."
    Y el botón con id "ev-submit" está deshabilitado

  @limpiar_evidencias
  Escenario: FA-01 - El alumno envía el formulario sin nombre
    Cuando el alumno adjunta el archivo "reporte.pdf"
    Y el alumno hace clic en el botón "Cargar actividad"
    Entonces la página muestra el texto "Ingresa un nombre para la actividad."
