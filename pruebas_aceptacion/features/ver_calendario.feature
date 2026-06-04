# language: es
# ID: CU-02  Nombre: Ver calendario semestral

Característica: CU-02 Ver calendario semestral
  Como alumno registrado en la plataforma
  Quiero acceder a la sección del calendario
  Para conocer las fechas límite de mis entregas y evaluaciones

  Antecedentes:
    Dado que el alumno específico "amer_cal" con contraseña "passcalendar" ha iniciado sesión
    Y el alumno tiene asignado el seminario del ciclo 4

  @limpiar_evidencias
  Escenario: Visualización exitosa del último calendario general publicado
    Dado que existe un calendario de actividades programado en la base de datos
    Cuando el alumno solicita consultar el calendario semestral
    Entonces se verifica el acceso correcto a los datos del calendario

  @limpiar_evidencias
  Escenario: Tolerancia del sistema cuando no se ha subido ningún calendario
    Dado que no hay ningún calendario registrado en el sistema
    Cuando el alumno solicita consultar el calendario semestral
    Entonces se confirma que el objeto retornado en la consulta es nulo