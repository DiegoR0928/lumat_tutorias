# language: es
# ID: CU-01  Nombre: Iniciar sesión

Característica: Iniciar sesión
    Como usuario del sistema de seguimiento de tutorias
    Quiero poder acceder a mi cuenta
    Para poder gestionar mis tutorias

    @limpiar_usuarios @limpiar_alumnos
    Escenario: Datos correctos
        Dado que ingreso en el sistema de tutorias
            Y escribo mi usuario "amer"
            Y escribo la contraseña "amer1234"
         Cuando presiono el botón "Entrar"
         Entonces puedo ver la sección "alumno" del sistema

    @limpiar_usuarios @limpiar_alumnos
    Escenario: Datos incorrectos
        Dado que ingreso en el sistema de tutorias
            Y escribo mi usuario "amer"
            Y escribo la contraseña "wrongpass"
         Cuando presiono el botón "Entrar"
         Entonces puedo ver un mensaje de error indicando que las credenciales son incorrectas