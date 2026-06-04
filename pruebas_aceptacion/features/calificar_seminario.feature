# language: es
# ID: CU-04  Nombre: Calificar seminario

Característica: CU-04 Calificar seminario
  Como docente/tutor registrado en el sistema
  Quiero asentar las calificaciones individuales y firmar el formulario
  Para que se calcule y registre la calificación final del seminario

  Antecedentes:
    Dado que el docente "tutor_carlos" con contraseña "tutor1234" ha iniciado sesión
    Y existe el seminario número 5 asignado al alumno "juan_perez"
    Y el panel de evaluación está listo con calificaciones pendientes

  @limpiar_evidencias
  Escenario: Registro exitoso de la calificación final por promedio completo
    Cuando el comite asienta las notas individuales 9.00, 8.50 y 9.50
    Y todos los miembros del comite firman el formulario
    Entonces se verifica en la base de datos que la calificación final del seminario es 9.00

  @limpiar_evidencias
  Escenario: Registro de calificación parcial cuando solo firma y califica el tutor
    Cuando el tutor asienta una nota individual de 9.00 y los demás quedan vacíos
    Y solo firma el tutor original
    Entonces se verifica en la base de datos que la calificación final del seminario es 9.00