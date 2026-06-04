# language: es
# ID: CU-03  Nombre: Cargar actividades

Característica: CU-03 Cargar actividades
  Como alumno registrado en el sistema
  Quiero cargar evidencias en formato PDF de mis actividades
  Para que queden registradas en mi seminario

  Antecedentes:
    Dado que el alumno "amer" con contraseña "amer1234" ha iniciado sesión
    Y el alumno tiene asignado el seminario número 4
    Y el formulario del comité para el seminario 4 tiene el estado general "pendiente"
    Y el alumno navega al panel del seminario 4

  @limpiar_evidencias
  Escenario: Carga exitosa de una actividad en formato PDF
    Cuando el alumno escribe "Reporte de avance" en el campo nombre
    Y el alumno adjunta el archivo "reporte.pdf"
    Y el alumno hace clic en el botón "Cargar actividad"
    Entonces se verifica que la actividad "Reporte de avance" quedó registrada en la base de datos

  @limpiar_evidencias
  Escenario: Carga fallida de una actividad con extensión inválida
    Cuando el alumno escribe "Imagen adjunta" en el campo nombre
    Y el alumno adjunta el archivo "imagen.jpg"
    Y el alumno hace clic en el botón "Cargar actividad"
    Entonces se verifica que la actividad "Imagen adjunta" no fue guardada en la base de datos