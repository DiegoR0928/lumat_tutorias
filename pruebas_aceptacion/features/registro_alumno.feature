# language: es

Característica: Registro de alumno
  Como administrador del sistema
  Quiero registrar nuevos alumnos mediante el formulario
  Para que puedan acceder al sistema con sus credenciales

  Escenario: Registro exitoso de un alumno con datos válidos
    Dado que estoy en la página de registro de alumno
    Cuando ingreso "juan123" en el campo "usuario"
    Y ingreso "juan@escuela.mx" en el campo "email"
    Y ingreso "Segura#2025" en el campo "contraseña"
    Y ingreso "Juan" en el campo "nombre"
    Y ingreso "Pérez" en el campo "apellido paterno"
    Y ingreso "García" en el campo "apellido materno"
    Y hago clic en el botón "Guardar"
    Entonces debo ver el mensaje "Alumno registrado con éxito"
    Y el formulario debe mostrarse vacío nuevamente

  Escenario: Registro fallido por nombre de usuario ya existente
    Dado que estoy en la página de registro de alumno
    Y el usuario "existente99" ya existe en el sistema
    Cuando ingreso "existente99" en el campo "usuario"
    Y ingreso "otro@escuela.mx" en el campo "email"
    Y ingreso "Segura#2025" en el campo "contraseña"
    Y ingreso "Pedro" en el campo "nombre"
    Y ingreso "López" en el campo "apellido paterno"
    Y ingreso "Martínez" en el campo "apellido materno"
    Y hago clic en el botón "Guardar"
    Entonces no debo ver el mensaje "Alumno registrado con éxito"
    Y debo ver un error en el campo "usuario"
