# language: es
# ID: CU-cambio-tutor  Nombre: Solicitar cambio de tutor

Característica: Solicitar cambio de tutor
  Como alumno registrado en el sistema
  Quiero solicitar un cambio de tutor
  Para que la coordinación lo evalúe y resuelva

  Antecedentes:
    Dado que el alumno "amerinaga" con contraseña "amer1234" ha iniciado sesión

  @limpiar_solicitudes
  Escenario: Envío exitoso de solicitud de cambio de tutor
    Dado que el alumno navega a la página de cambio de tutor
    Cuando el alumno escribe "Mi tutor no está disponible para reuniones." en el campo motivo
    Y el alumno hace clic en el botón de enviar solicitud
    Entonces la solicitud fue enviada exitosamente

#   Escenario: El botón está deshabilitado si el motivo está vacío
#     Dado que el alumno navega a la página de cambio de tutor
#     Entonces el botón con id "ct-submit" está deshabilitado
#     Cuando el alumno escribe "Necesito un tutor con otra especialidad." en el campo motivo
#     Entonces el botón con id "ct-submit" está habilitado

#   Escenario: El alumno intenta enviar sin escribir motivo
#     Dado que el alumno navega a la página de cambio de tutor
#     Cuando el alumno hace clic en el botón de enviar sin motivo
#     Entonces el mensaje de error "Debes indicar el motivo de la solicitud." es visible en la página

  @limpiar_solicitudes
  Escenario: El formulario se bloquea si ya hay una solicitud pendiente
    Dado que el alumno ya tiene una solicitud pendiente
    Y el alumno navega a la página de cambio de tutor
    Entonces la página muestra el texto "solicitud en estado pendiente"
    Y el botón con id "ct-submit" está deshabilitado
