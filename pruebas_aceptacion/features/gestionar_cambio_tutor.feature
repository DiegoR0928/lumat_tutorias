# language: es
Característica: Gestionar Cambio de Tutor

  Antecedentes:
    Dado un usuario administrador autenticado
    Y existe una solicitud de cambio de tutor pendiente

  @limpiar_usuarios @limpiar_alumnos @limpiar_docentes @limpiar_solicitudes
  Escenario: Aprobacion exitosa cambiando el tutor
    Cuando ingreso a la gestion de cambio de tutor
    Y selecciono un nuevo docente elegible
    Y presiono el boton aprobar cambio de tutor
    Entonces la solicitud cambia a estado aprobada

  @limpiar_usuarios @limpiar_alumnos @limpiar_docentes @limpiar_solicitudes
  Escenario: Rechazo exitoso sin seleccionar docente
    Cuando ingreso a la gestion de cambio de tutor
    Y presiono el boton rechazar cambio de tutor
    Entonces la solicitud cambia a estado rechazada

  @limpiar_usuarios @limpiar_alumnos @limpiar_docentes @limpiar_solicitudes
  Escenario: Intento de aprobacion sin seleccionar docente
    Cuando ingreso a la gestion de cambio de tutor
    Y presiono el boton aprobar cambio de tutor
    Entonces veo un mensaje de error indicando elegir un tutor

  @limpiar_usuarios @limpiar_alumnos @limpiar_docentes @limpiar_solicitudes
  Escenario: Intento de aprobacion con docente ya presente en el comite
    Cuando ingreso a la gestion de cambio de tutor
    Y selecciono un docente que ya pertenece al comite
    Y presiono el boton aprobar cambio de tutor
    Entonces veo un mensaje de error por miembro activo en comite