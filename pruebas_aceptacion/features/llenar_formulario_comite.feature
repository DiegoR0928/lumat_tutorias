# language: es
Característica: Llenado del Informe del Comité Tutor
  Como docente con rol de Tutor en el sistema Lumat Tutorias
  Quiero completar el contenido del informe del comité
  Para registrar las observaciones y el dictamen del estudiante.

  Antecedentes:
    Dado que existe un docente registrado como tutor y dos como miembros
    Y existe un estudiante en el semestre 4 con un seminario pendiente

  @limpiar_usuarios @limpiar_docentes @limpiar_alumnos
  Escenario: El Tutor guarda el informe exitosamente con todos los campos llenos
    Dado que el tutor ha iniciado sesión en el sistema
    Y se encuentra en la pantalla de "Mis Seminarios"
    Cuando hace clic en el seminario del estudiante Luis Pérez
    Y completa los campos de observaciones, dictamen, encuentros y propuestas
    Y hace clic en el botón "Guardar informe"
    Entonces el sistema debe mostrar el mensaje de éxito "Informe guardado correctamente."

  @limpiar_usuarios @limpiar_docentes @limpiar_alumnos
  Escenario: El Tutor intenta guardar el informe con campos vacíos obligatorios
    Dado que el tutor ha iniciado sesión en el sistema
    Y se encuentra en el detalle del seminario de Luis Pérez
    Cuando borra o deja vacíos los campos del informe
    Y hace clic en el botón "Guardar informe"
    Entonces el sistema debe denegar el guardado mostrando un mensaje de error o validación