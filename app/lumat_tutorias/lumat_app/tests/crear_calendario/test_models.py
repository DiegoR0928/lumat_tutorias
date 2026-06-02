from datetime import date
from django.test import TestCase
from lumat_app.models import CalendarioGenerado


class TestCalendarioGeneradoModel(TestCase):

    def setUp(self):
        self.cal_1 = CalendarioGenerado.objects.create(
            nombre="Periodo A",
            fecha_inicio=date(2026, 6, 1),
            fecha_fin=date(2026, 6, 30)
        )

    def test_creacion_calendario_guardado_exitoso(self):
        self.assertEqual(self.cal_1.nombre, "Periodo A")
        self.assertEqual(self.cal_1.fecha_inicio, date(2026, 6, 1))
        self.assertEqual(self.cal_1.fecha_fin, date(2026, 6, 30))

    def test_string_representation(self):
        fecha_str = self.cal_1.fecha_creacion.strftime('%d/%m/%Y')
        expected_str = f"Periodo A ({fecha_str})"
        self.assertEqual(str(self.cal_1), expected_str)

    def test_ordenamiento_por_defecto_mas_reciente_primero(self):
        cal_2 = CalendarioGenerado.objects.create(
            nombre="Periodo B",
            fecha_inicio=date(2026, 7, 1),
            fecha_fin=date(2026, 7, 30)
        )
        calendarios = CalendarioGenerado.objects.all()
        self.assertEqual(calendarios[0], cal_2)
        self.assertEqual(calendarios[1], self.cal_1)
