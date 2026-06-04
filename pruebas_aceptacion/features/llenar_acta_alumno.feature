# language: es
# ID: CU-06  Nombre: Llenar acta del alumno

Característica: CU-06 Llenar acta del alumno
  Como alumno registrado en el sistema
  Quiero registrar mis actividades semestrales, reuniones y plan de trabajo
  Para que queden guardados en mi acta del alumno una vez habilitada por el comité

  Antecedentes:
    Dado que el alumno específico "amer_alumno" con contraseña "alumno1234" ha iniciado sesión
    Y el alumno tiene asignado el seminario del ciclo 4

  @limpiar_evidencias @limpiar_alumnos
  Escenario: Registro exitoso de los datos de acta cuando el comité ya evaluó el seminario
    Dado que el formulario del comité para el seminario 4 tiene el estado general "completo"
    Cuando el alumno registra sus actividades con reuniones de tutor 6 y reuniones de comité 3
    Y el alumno asienta su plan siguiente "Finalizar la redacción del capítulo de pruebas"
    Entonces se verifica en la base de datos que el acta del alumno se guardó exitosamente

  @limpiar_evidencias @limpiar_alumnos
  Escenario: Intento fallido de registrar los datos de acta si el comité no ha completado el formulario
    Dado que el formulario del comité para el seminario 4 tiene el estado general "pendiente"
    Cuando el alumno intenta forzar el registro de sus actividades y plan de trabajo
    Entonces se verifica en la base de datos que no se creó ningún registro de acta para el alumno