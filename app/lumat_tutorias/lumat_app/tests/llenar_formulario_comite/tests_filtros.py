from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.contrib.auth.models import User
from django.db.models import Q

from lumat_app.models import Seminario, Alumno, Comite, FormularioComite, Docente
from lumat_app.views_docente import (
    _filtrar_por_busqueda,
    _obtener_estado_formulario,
    _filtrar_por_rol_y_estado,
    _combinar_roles
)


# ==================== HELPERS ====================

class BaseFiltrosTest(TestCase):
    """Clase base con configuración común para pruebas de filtros"""

    def setUp(self):
        self._crear_usuarios()
        self._crear_docentes()
        self._crear_alumnos()
        self._crear_comite()
        self._crear_seminarios()
        self._crear_formularios()

    def _crear_usuarios(self):
        """Crear usuarios base"""
        # Alumnos
        self.user_alumno1 = User.objects.create_user(
            username='alumno_filtro', password='testpass123', email='alumno@test.com'
        )
        self.user_alumno2 = User.objects.create_user(
            username='alumno_filtro2', password='testpass123', email='alumno2@test.com'
        )

        # Docentes
        self.user_tutor = User.objects.create_user(
            username='tutor_filtro', password='testpass123', email='tutor@test.com'
        )
        self.user_miembro1 = User.objects.create_user(
            username='miembro1_filtro', password='testpass123', email='miembro1@test.com'
        )
        self.user_miembro2 = User.objects.create_user(
            username='miembro2_filtro', password='testpass123', email='miembro2@test.com'
        )

    def _crear_docentes(self):
        """Crear docentes"""
        self.tutor = Docente.objects.create(
            user=self.user_tutor, nombre="Carlos", apellido_paterno="Lopez",
            apellido_materno="Garcia", correo="tutor@test.com"
        )
        self.miembro1 = Docente.objects.create(
            user=self.user_miembro1, nombre="Maria", apellido_paterno="Martinez",
            apellido_materno="Rodriguez", correo="miembro1@test.com"
        )
        self.miembro2 = Docente.objects.create(
            user=self.user_miembro2, nombre="Jose", apellido_paterno="Sanchez",
            apellido_materno="Perez", correo="miembro2@test.com"
        )

    def _crear_alumnos(self):
        """Crear alumnos"""
        self.alumno1 = Alumno.objects.create(
            user=self.user_alumno1, nombre="Juan", apellido_paterno="Perez",
            apellido_materno="Lopez", matricula="20220001", semestre="5", correo="juan@test.com"
        )
        self.alumno2 = Alumno.objects.create(
            user=self.user_alumno2, nombre="Maria", apellido_paterno="Gomez",
            apellido_materno="Lopez", matricula="20220002", semestre="5", correo="maria@test.com"
        )

    def _crear_comite(self):
        """Crear comité"""
        self.comite = Comite.objects.create(
            tutor=self.tutor, miembro1=self.miembro1, miembro2=self.miembro2
        )

    def _crear_seminarios(self):
        """Crear seminarios"""
        self.seminario1 = Seminario.objects.create(
            numero=5, periodo=1, fecha=date(2024, 3, 15), hora="10:00",
            alumno=self.alumno1, comite=self.comite
        )
        self.seminario2 = Seminario.objects.create(
            numero=5, periodo=1, fecha=date(2024, 3, 15), hora="11:00",
            alumno=self.alumno2, comite=self.comite
        )

    def _crear_formularios(self):
        """Crear formularios con diferentes estados"""
        self.formulario_completo = FormularioComite.objects.create(
            seminario=self.seminario1,
            firma_tutor=True, firma_miembro1=True, firma_miembro2=True,
            calificacion_tutor=Decimal("8.0"), calificacion_miembro1=Decimal("8.0"),
            calificacion_miembro2=Decimal("8.0")
        )
        self.formulario_completo.save()  # Forzar recalcular estado

        self.formulario_pendiente = FormularioComite.objects.create(
            seminario=self.seminario2
        )

    def _get_querysets(self):
        """Helper para obtener querysets de tutor y miembro"""
        como_tutor = Seminario.objects.filter(comite__tutor=self.tutor)
        como_miembro = Seminario.objects.filter(
            Q(comite__miembro1=self.tutor) | Q(comite__miembro2=self.tutor)
        )
        return como_tutor, como_miembro


class ObtenerEstadoFormularioTest(BaseFiltrosTest):
    """Pruebas para _obtener_estado_formulario"""

    def test_estado_completo_cuando_tiene_formulario(self):
        self.formulario_completo.refresh_from_db()
        estado = _obtener_estado_formulario(self.seminario1)
        self.assertEqual(estado, 'completo')

    def test_estado_pendiente_cuando_no_tiene_formulario(self):
        seminario_sin_form = Seminario.objects.create(
            numero=6, periodo=1, fecha=date(2024, 4, 15), hora="12:00",
            alumno=self.alumno1, comite=self.comite
        )
        estado = _obtener_estado_formulario(seminario_sin_form)
        self.assertEqual(estado, 'pendiente')

    def test_estado_pendiente_cuando_formulario_pendiente(self):
        estado = _obtener_estado_formulario(self.seminario2)
        self.assertEqual(estado, 'pendiente')


class FiltrarPorBusquedaTest(BaseFiltrosTest):
    """Pruebas para _filtrar_por_busqueda"""

    def test_filtrar_por_matricula(self):
        como_tutor, como_miembro = self._get_querysets()
        resultado = _filtrar_por_busqueda(como_tutor, como_miembro, "20220001")

        self.assertEqual(len(resultado), 1)
        self.assertEqual(
            resultado[0]['seminario'].alumno.matricula, "20220001")

    def test_filtrar_sin_resultados(self):
        como_tutor, como_miembro = self._get_querysets()
        resultado = _filtrar_por_busqueda(
            como_tutor, como_miembro, "MATRICULA_INEXISTENTE")
        self.assertEqual(len(resultado), 0)


class FiltrarPorRolYEstadoTest(BaseFiltrosTest):
    """Pruebas para _filtrar_por_rol_y_estado"""

    def test_filtrar_por_rol_tutor(self):
        como_tutor, como_miembro = self._get_querysets()
        resultado = _filtrar_por_rol_y_estado(
            como_tutor, como_miembro, 'tutor', 'todos')

        for item in resultado:
            self.assertEqual(item['rol'], 'tutor')

    def test_filtrar_por_rol_miembro(self):
        # Crear seminario donde el tutor es miembro
        comite_dual = Comite.objects.create(
            tutor=self.miembro1, miembro1=self.tutor, miembro2=self.miembro2
        )
        Seminario.objects.create(
            numero=6, periodo=1, fecha=date(2024, 3, 16), hora="12:00",
            alumno=self.alumno1, comite=comite_dual
        )

        como_tutor, como_miembro = self._get_querysets()
        resultado = _filtrar_por_rol_y_estado(
            como_tutor, como_miembro, 'miembro', 'todos')

        roles = set(item['rol'] for item in resultado)
        self.assertIn('miembro', roles)

    def test_filtrar_por_rol_todos(self):
        # Crear seminario donde el tutor es miembro
        comite_dual = Comite.objects.create(
            tutor=self.miembro1, miembro1=self.tutor, miembro2=self.miembro2
        )
        Seminario.objects.create(
            numero=6, periodo=1, fecha=date(2024, 3, 16), hora="12:00",
            alumno=self.alumno1, comite=comite_dual
        )

        como_tutor, como_miembro = self._get_querysets()
        resultado = _filtrar_por_rol_y_estado(
            como_tutor, como_miembro, 'todos', 'todos')

        roles = set(item['rol'] for item in resultado)
        self.assertIn('tutor', roles)

    def test_filtrar_por_estado_completados(self):
        como_tutor, como_miembro = self._get_querysets()
        resultado = _filtrar_por_rol_y_estado(
            como_tutor, como_miembro, 'todos', 'completados')

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]['seminario'], self.seminario1)
        # El estado no está en el diccionario, verificamos con la función auxiliar
        estado = _obtener_estado_formulario(resultado[0]['seminario'])
        self.assertEqual(estado, 'completo')

    def test_filtrar_por_estado_pendientes(self):
        como_tutor, como_miembro = self._get_querysets()
        resultado = _filtrar_por_rol_y_estado(
            como_tutor, como_miembro, 'todos', 'pendientes')

        # Verificar que hay al menos un seminario pendiente
        seminarios_pendientes = [
            item for item in resultado
            if _obtener_estado_formulario(item['seminario']) == 'pendiente'
        ]
        self.assertGreaterEqual(len(seminarios_pendientes), 1)


class CombinarRolesTest(BaseFiltrosTest):
    """Pruebas para _combinar_roles"""

    def test_evitar_duplicados_por_seminario(self):
        tutores = [{'seminario': self.seminario1, 'rol': 'tutor'}]
        miembros = [{'seminario': self.seminario1, 'rol': 'miembro'}]

        resultado = _combinar_roles(tutores, miembros)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]['rol'], 'tutor')  # Prioriza tutor

    # def test_ordenamiento_correcto(self):
    #     """Probar que _combinar_roles ordena los resultados"""
    #     tutores = [
    #         {'seminario': self.seminario2, 'rol': 'tutor'},
    #         {'seminario': self.seminario1, 'rol': 'tutor'}
    #     ]

    #     resultado = _combinar_roles(tutores, [])

    #     # Ambos seminarios deben estar presentes, verificar que están ordenados
    #     self.assertEqual(len(resultado), 2)
    #     # Verificar que el orden es correcto (por número y periodo)
    #     self.assertEqual(resultado[0]['seminario'].numero, self.seminario1.numero)
    #     self.assertEqual(resultado[0]['seminario'].alumno, self.alumno1)

    def test_combinacion_sin_duplicados(self):
        tutores = [{'seminario': self.seminario1, 'rol': 'tutor'}]
        miembros = [{'seminario': self.seminario2, 'rol': 'miembro'}]

        resultado = _combinar_roles(tutores, miembros)

        self.assertEqual(len(resultado), 2)
        roles = [item['rol'] for item in resultado]
        self.assertIn('tutor', roles)
        self.assertIn('miembro', roles)

    def test_resultado_vacio_cuando_ambos_vacios(self):
        resultado = _combinar_roles([], [])
        self.assertEqual(len(resultado), 0)
