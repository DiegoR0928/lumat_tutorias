# language: es
Característica: Crear calendario automatizado

  Antecedentes:
    Dado un usuario administrador autenticado

  @limpiar_usuarios @limpiar_alumnos @limpiar_docentes @limpiar_solicitudes
  Escenario: Generacion exitosa de calendario
    Dado existen 2 seminarios registrados
    Cuando ingreso al formulario de calendario
    Y selecciono la fecha inicial "2026-06-10" y final "2026-06-20"
    Y presiono el boton de generar calendario
    Entonces soy redirigido al formulario con un mensaje de exito
    Y se muestra el nuevo calendario publicado

  @limpiar_usuarios @limpiar_alumnos @limpiar_docentes
  Escenario: Intento de generacion con fecha inicial posterior a la final
    Dado existen 2 seminarios registrados
    Cuando ingreso al formulario de calendario
    Y selecciono la fecha inicial "2026-06-20" y final "2026-06-10"
    Y presiono el boton de generar calendario
    Entonces soy redirigido al formulario con un mensaje de error

  @limpiar_usuarios @limpiar_alumnos @limpiar_docentes
  Escenario: Intento de generacion con insuficientes slots horarios
    Dado existen 10 seminarios registrados
    Cuando ingreso al formulario de calendario
    Y selecciono la fecha inicial "2026-06-06" y final "2026-06-07"
    Y presiono el boton de generar calendario
    Entonces soy redirigido al formulario con un mensaje de error