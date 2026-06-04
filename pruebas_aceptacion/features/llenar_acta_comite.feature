# language: es
# ID: CU-05  Nombre: Llenar acta del comite

Característica: CU-05 Llenar acta del comite
  Como tutor asignado a un seminario
  Quiero registrar los comentarios, observaciones y dictamen del desempeño del alumno
  Para que queden guardados en el informe del formulario del comité

  Antecedentes:
    Dado que el tutor "tutor_carlos" con contraseña "tutor1234" ha iniciado sesión en la plataforma
    Y existe un seminario activo número 4 para el alumno "pedro_infante" con un comité asignado
    Y el panel tiene un formulario de acta en estado "pendiente"

  @limpiar_evidencias
  Escenario: Registro exitoso del dictamen e informe del comité por parte del tutor
    Cuando el tutor redacta el reporte con encuentra "Excelente avance" y observaciones "Ninguna"
    Y el tutor asienta el dictamen "Aprobado - Continúa"
    Entonces se verifica en la base de datos que el informe del comité guardó el dictamen correctamente

  @limpiar_evidencias
  Escenario: Intento fallido de guardar el acta con el campo dictamen vacío
    Cuando el tutor redacta el reporte con encuentra "Avance regular" y observaciones "Revisar"
    Y el tutor deja el campo dictamen vacío al guardar
    Entonces se verifica en la base de datos que el dictamen en el formulario sigue estando vacío