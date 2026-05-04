Característica: Editar la información del alumno
    Como alumno del sistema
    Quiero poder editar mi información personal
    Para mantener mis datos actualizados en el sistema

    Escenario: Edición exitosa de la información del alumno
        Dado que he iniciado sesión como alumno con la cuenta "prueba" y contraseña "amer1234"
        Cuando navego a la página de edición de perfil
            Y actualizo mi "matricula" a "123456789"
            Y hago clic en el botón de guardar
        Entonces debería ver el mensaje "Perfil actualizado exitosamente" y mi "matricula" actualizado a "123456789"

    Escenario: Intento de editar la información del alumno con datos inválidos
        Dado que he iniciado sesión como alumno con la cuenta "prueba" y contraseña "amer1234"
        Cuando navego a la página de edición de perfil
            Y actualizo mi "correo" a "correo_invalido"
            Y hago clic en el botón de guardar
        Entonces debería ver un mensaje de error indicando que los datos son inválidos

    Escenario: Edición de la información dejando un campo obligatorio vacío
        Dado que he iniciado sesión como alumno con la cuenta "prueba" y contraseña "amer1234"
        Cuando navego a la página de edición de perfil
            Y dejo el campo de nombre vacío
            Y hago clic en el botón de guardar
        Entonces el campo "nombre" debería mostrar un error

    Escenario: Cambio exitoso de contraseña
        Dado que he iniciado sesión como alumno con la cuenta "prueba" y contraseña "amer1234"
        Cuando navego a la página de cambio de contraseña
        Y ingreso la contraseña actual "amer1234"
        Y ingreso la nueva contraseña "Nueva1234!"
        Y confirmo la nueva contraseña "Nueva1234!"
        Y hago clic en el botón de actualizar contraseña
        Entonces debería ver el mensaje "Contraseña actualizada exitosamente"

    Escenario: Error al cambiar contraseña por contraseña actual incorrecta
        Dado que he iniciado sesión como alumno con la cuenta "prueba" y contraseña "Nueva1234!"
        Cuando navego a la página de cambio de contraseña
        Y ingreso la contraseña actual "incorrecta123"
        Y ingreso la nueva contraseña "Nueva1234!"
        Y confirmo la nueva contraseña "Nueva1234!"
        Y hago clic en el botón de actualizar contraseña
        Entonces el campo "old_password" debería mostrar un error
