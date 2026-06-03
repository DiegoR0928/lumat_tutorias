# language: es
Característica: Verificar Estadisticas de Panel

  @limpiar_usuarios @limpiar_alumnos @limpiar_docentes
  Escenario: Visualizar correctamente las metricas en el dashboard
    Dado un usuario administrador autenticado
    Y existen 3 alumnos y 2 docentes registrados
    Cuando ingreso al panel de estadisticas
    Entonces el dashboard muestra "3" alumnos y "2" docentes