from django.test import TestCase
from django.contrib.auth.models import User
from django.db.models import Q
from decimal import Decimal
from lumat_app.models import Seminario, Alumno, Comite, FormularioComite, Docente
from lumat_app.views_docente import (
    _filtrar_por_busqueda,
    _obtener_estado_formulario,
    _filtrar_por_rol_y_estado,
    _combinar_roles
)
from datetime import date


class FiltrosFuncionesTest(TestCase):
    """Pruebas para las funciones de filtrado"""

    def setUp(self):
        # Crear usuario para el alumno
        self.user_alumno = User.objects.create_user(
            username='alumno_filtro',
            password='testpass123',
            email='alumno@test.com'
        )

        # Crear alumno
        self.alumno = Alumno.objects.create(
            user=self.user_alumno,
            nombre="Juan",
            apellido_paterno="Perez",
            apellido_materno="Lopez",
            matricula="20220001",
            semestre="5",
            correo="juan@test.com"
        )

        # Crear otro alumno para pruebas de búsqueda
        self.user_alumno2 = User.objects.create_user(
            username='alumno_filtro2',
            password='testpass123',
            email='alumno2@test.com'
        )
        self.alumno2 = Alumno.objects.create(
            user=self.user_alumno2,
            nombre="Maria",
            apellido_paterno="Gomez",
            apellido_materno="Lopez",
            matricula="20220002",
            semestre="5",
            correo="maria@test.com"
        )

        # Crear usuarios para docentes
        self.user_tutor = User.objects.create_user(
            username='tutor_filtro',
            password='testpass123',
            email='tutor@test.com'
        )
        self.user_miembro1 = User.objects.create_user(
            username='miembro1_filtro',
            password='testpass123',
            email='miembro1@test.com'
        )
        self.user_miembro2 = User.objects.create_user(
            username='miembro2_filtro',
            password='testpass123',
            email='miembro2@test.com'
        )

        # Crear docentes
        self.tutor = Docente.objects.create(
            user=self.user_tutor,
            nombre="Carlos",
            apellido_paterno="Lopez",
            apellido_materno="Garcia",
            correo="tutor@test.com"
        )

        self.miembro1 = Docente.objects.create(
            user=self.user_miembro1,
            nombre="Maria",
            apellido_paterno="Martinez",
            apellido_materno="Rodriguez",
            correo="miembro1@test.com"
        )

        self.miembro2 = Docente.objects.create(
            user=self.user_miembro2,
            nombre="Jose",
            apellido_paterno="Sanchez",
            apellido_materno="Perez",
            correo="miembro2@test.com"
        )

        # Crear comité
        self.comite = Comite.objects.create(
            tutor=self.tutor,
            miembro1=self.miembro1,
            miembro2=self.miembro2
        )

        # Crear seminarios
        self.seminario1 = Seminario.objects.create(
            numero=5,
            periodo=1,
            fecha=date(2024, 3, 15),
            hora="10:00",
            alumno=self.alumno,
            comite=self.comite
        )

        self.seminario2 = Seminario.objects.create(
            numero=5,
            periodo=1,
            fecha=date(2024, 3, 15),
            hora="11:00",
            alumno=self.alumno2,
            comite=self.comite
        )

        # Crear formularios con el estado correcto
        self.formulario1 = FormularioComite.objects.create(
            seminario=self.seminario1,
            firma_tutor=True,
            firma_miembro1=True,
            firma_miembro2=True,
            calificacion_tutor=Decimal("8.0"),
            calificacion_miembro1=Decimal("8.0"),
            calificacion_miembro2=Decimal("8.0")
        )
        # Forzar recalcular estado
        self.formulario1.save()

        self.formulario2 = FormularioComite.objects.create(
            seminario=self.seminario2
        )

    def test_obtener_estado_formulario_con_formulario(self):
        """Probar _obtener_estado_formulario cuando el seminario tiene formulario"""
        # Refrescar desde DB para obtener el estado actual
        self.formulario1.refresh_from_db()
        estado = _obtener_estado_formulario(self.seminario1)
        self.assertEqual(estado, 'completo')

    def test_obtener_estado_formulario_sin_formulario(self):
        """Probar _obtener_estado_formulario cuando el seminario NO tiene formulario"""
        # Crear seminario sin formulario
        seminario_sin_form = Seminario.objects.create(
            numero=6,
            periodo=1,
            fecha=date(2024, 4, 15),
            hora="12:00",
            alumno=self.alumno,
            comite=self.comite
        )
        estado = _obtener_estado_formulario(seminario_sin_form)
        self.assertEqual(estado, 'pendiente')

    def test_obtener_estado_formulario_con_formulario_pendiente(self):
        """Probar _obtener_estado_formulario cuando el formulario está pendiente"""
        estado = _obtener_estado_formulario(self.seminario2)
        self.assertEqual(estado, 'pendiente')

    def test_filtrar_por_busqueda_por_matricula(self):
        """Probar _filtrar_por_busqueda filtrando por matrícula"""
        # Crear querysets simulados
        como_tutor = Seminario.objects.filter(comite__tutor=self.tutor)
        como_miembro = Seminario.objects.filter(
            Q(comite__miembro1=self.tutor) | Q(comite__miembro2=self.tutor)
        )

        resultado = _filtrar_por_busqueda(como_tutor, como_miembro, "20220001")

        # Debe encontrar el seminario del alumno con esa matrícula
        self.assertEqual(len(resultado), 1)
        self.assertEqual(
            resultado[0]['seminario'].alumno.matricula, "20220001")

    def test_filtrar_por_busqueda_sin_resultados(self):
        """Probar _filtrar_por_busqueda cuando no hay coincidencias"""
        como_tutor = Seminario.objects.filter(comite__tutor=self.tutor)
        como_miembro = Seminario.objects.filter(
            Q(comite__miembro1=self.tutor) | Q(comite__miembro2=self.tutor)
        )

        resultado = _filtrar_por_busqueda(
            como_tutor, como_miembro, "MATRICULA_INEXISTENTE")

        self.assertEqual(len(resultado), 0)

    def test_filtrar_por_rol_y_estado_rol_tutor(self):
        """Probar _filtrar_por_rol_y_estado con rol='tutor'"""
        como_tutor = Seminario.objects.filter(comite__tutor=self.tutor)
        como_miembro = Seminario.objects.filter(
            Q(comite__miembro1=self.tutor) | Q(comite__miembro2=self.tutor)
        )

        resultado = _filtrar_por_rol_y_estado(
            como_tutor, como_miembro, 'tutor', 'todos')

        # Solo debe incluir seminarios donde es tutor
        for item in resultado:
            self.assertEqual(item['rol'], 'tutor')

    def test_filtrar_por_rol_y_estado_rol_miembro(self):
        """Probar _filtrar_por_rol_y_estado con rol='miembro'"""
        # Necesitamos un seminario donde el tutor sea miembro también
        # Para esto, creamos un seminario donde el tutor también es miembro
        # comite2 = Comite.objects.create(
        #     tutor=self.miembro1,  # Tutor diferente
        #     miembro1=self.tutor,   # El tutor original como miembro1
        #     miembro2=self.miembro2
        # )

        # seminario_miembro = Seminario.objects.create(
        #     numero=6,
        #     periodo=1,
        #     fecha=date(2024, 3, 16),
        #     hora="12:00",
        #     alumno=self.alumno,
        #     comite=comite2
        # )

        como_tutor = Seminario.objects.filter(comite__tutor=self.tutor)
        como_miembro = Seminario.objects.filter(
            Q(comite__miembro1=self.tutor) | Q(comite__miembro2=self.tutor)
        )

        resultado = _filtrar_por_rol_y_estado(
            como_tutor, como_miembro, 'miembro', 'todos')

        # Verificar que hay resultados con rol miembro
        hay_miembro = any(item['rol'] == 'miembro' for item in resultado)
        self.assertTrue(hay_miembro)

    def test_filtrar_por_rol_y_estado_rol_todos(self):
        """Probar _filtrar_por_rol_y_estado con rol='todos'"""
        # Crear un seminario donde el tutor también es miembro
        # comite2 = Comite.objects.create(
        #     tutor=self.miembro1,
        #     miembro1=self.tutor,
        #     miembro2=self.miembro2
        # )

        # seminario_miembro = Seminario.objects.create(
        #     numero=6,
        #     periodo=1,
        #     fecha=date(2024, 3, 16),
        #     hora="12:00",
        #     alumno=self.alumno,
        #     comite=comite2
        # )

        como_tutor = Seminario.objects.filter(comite__tutor=self.tutor)
        como_miembro = Seminario.objects.filter(
            Q(comite__miembro1=self.tutor) | Q(comite__miembro2=self.tutor)
        )

        resultado = _filtrar_por_rol_y_estado(
            como_tutor, como_miembro, 'todos', 'todos')

        # Debe incluir ambos roles cuando hay ambos
        roles = set(item['rol'] for item in resultado)
        self.assertIn('tutor', roles)

    def test_filtrar_por_rol_y_estado_completados(self):
        """Probar _filtrar_por_rol_y_estado con estado='completados'"""
        como_tutor = Seminario.objects.filter(comite__tutor=self.tutor)
        como_miembro = Seminario.objects.filter(
            Q(comite__miembro1=self.tutor) | Q(comite__miembro2=self.tutor)
        )

        resultado = _filtrar_por_rol_y_estado(
            como_tutor, como_miembro, 'todos', 'completados')

        # El seminario1 debe estar completo
        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]['seminario'], self.seminario1)

    def test_filtrar_por_rol_y_estado_pendientes(self):
        """Probar _filtrar_por_rol_y_estado con estado='pendientes'"""
        como_tutor = Seminario.objects.filter(comite__tutor=self.tutor)
        como_miembro = Seminario.objects.filter(
            Q(comite__miembro1=self.tutor) | Q(comite__miembro2=self.tutor)
        )

        resultado = _filtrar_por_rol_y_estado(
            como_tutor, como_miembro, 'todos', 'pendientes')

        # El seminario2 debe estar pendiente
        seminarios_pendientes = [item['seminario'] for item in resultado if _obtener_estado_formulario(
            item['seminario']) == 'pendiente']
        self.assertGreaterEqual(len(seminarios_pendientes), 1)

    def test_combinar_roles_evita_duplicados(self):
        """Probar que _combinar_roles evita duplicados basados en pk"""
        # Crear listas con el mismo seminario
        tutores = [{'seminario': self.seminario1, 'rol': 'tutor'}]
        miembros = [{'seminario': self.seminario1, 'rol': 'miembro'}]

        resultado = _combinar_roles(tutores, miembros)

        # Debe tener solo un elemento (evita duplicado)
        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]['rol'], 'tutor')  # Prioriza tutor

    def test_combinar_roles_ordena_correctamente(self):
        """Probar que _combinar_roles ordena los resultados"""
        tutores = [
            {'seminario': self.seminario2, 'rol': 'tutor'},
            {'seminario': self.seminario1, 'rol': 'tutor'}
        ]

        resultado = _combinar_roles(tutores, [])

        # Debe estar ordenado por numero y periodo
        self.assertEqual(
            resultado[0]['seminario'].numero, self.seminario1.numero)
