# language: es
Característica: Gestión de Comités en el panel de administración
  Como administrador del sistema
  Quiero poder crear un comité desde el panel de control
  Para poder organizar los seminarios de los alumnos

  Escenario: Creación exitosa de un comité con 3 docentes
    Dado que existen tres docentes en el sistema
      Y he iniciado sesión como superusuario
    Cuando navego a la página de crear comité
      Y selecciono a los tres docentes
      Y hago clic en guardar
    Entonces debería ver el mensaje de éxito en la pantalla
  
  Escenario: Intento de crear un comité sin seleccionar todos los docentes
    Dado que existen tres docentes en el sistema
      Y he iniciado sesión como superusuario
    Cuando navego a la página de crear comité
      Y selecciono a "Diego Gomez" como tutor
      Y dejo los campos de miembros vacíos
      Y hago clic en guardar
    Entonces el sistema debería resaltar los campos obligatorios y no guardar el comité