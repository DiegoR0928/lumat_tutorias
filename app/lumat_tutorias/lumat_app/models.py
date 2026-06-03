import os
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from decimal import Decimal, ROUND_HALF_UP
from django.core.files.base import ContentFile


class Alumno(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    matricula = models.CharField(
        max_length=8, unique=True, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100)
    semestre = models.CharField(max_length=50, default=1)
    correo = models.EmailField()

    def __str__(self):
        return f"{self.nombre} {self.apellido_paterno} ({self.matricula})"


class Docente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100)
    correo = models.EmailField()
    firma = models.ImageField(upload_to='firmas/', )

    def __str__(self):
        return f"{self.nombre} {self.apellido_paterno}"


class Comite(models.Model):
    tutor = models.ForeignKey(Docente, on_delete=models.CASCADE)
    miembro1 = models.ForeignKey(
        Docente,
        on_delete=models.CASCADE,
        related_name="miembro1",
        verbose_name="Primer miembro",
    )
    miembro2 = models.ForeignKey(
        Docente,
        on_delete=models.CASCADE,
        related_name="miembro2",
        verbose_name="Segundo miembro",
    )

    def clean(self):
        docentes = [self.tutor_id, self.miembro1_id, self.miembro2_id]
        if len(set(docentes)) != 3:
            raise ValidationError(
                "Los tres docentes del comité deben ser distintos.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.id:
            return f"Comité {self.id}"
        return "Comité Nuevo"


class Seminario(models.Model):
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE)
    comite = models.ForeignKey(Comite, on_delete=models.CASCADE)
    fecha = models.DateField(null=True, blank=True)
    hora = models.TimeField(null=True, blank=True)
    calificacion = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True)
    actaComite = models.FileField(upload_to='actas/', null=True, blank=True)
    actaAlumno = models.FileField(
        upload_to='actas_alumno/', null=True, blank=True)

    # Número del seminario (1-8)
    numero = models.PositiveSmallIntegerField()

    # Intento del seminario
    periodo = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['numero', 'periodo']

        constraints = [
            models.UniqueConstraint(
                fields=['alumno', 'numero', 'periodo'],
                name='unique_seminario_periodo'
            )
        ]

    def __str__(self):
        return (
            f"Seminario"
            f"(Periodo {self.periodo}) - "
            f"{self.alumno}"
        )


class CalifSeminario(models.Model):
    seminario = models.ForeignKey(Seminario, on_delete=models.CASCADE)
    docente = models.ForeignKey(Docente, on_delete=models.CASCADE)
    calificacion = models.DecimalField(max_digits=4, decimal_places=2)

    def __str__(self):
        return f"Calificación de {self.docente.__str__()} para \
        {self.seminario.__str__()}"


class CalendarioGenerado(models.Model):
    nombre = models.CharField(
        max_length=150, verbose_name="Nombre del Periodo")
    fecha_inicio = models.DateField(verbose_name="Fecha Inicial")
    fecha_fin = models.DateField(verbose_name="Fecha Final")
    # Almacena el PDF dentro de la carpeta media/calendarios_guardados/
    archivo_pdf = models.FileField(
        upload_to='calendarios_guardados/', verbose_name="Archivo PDF")
    fecha_creacion = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Generación")

    class Meta:
        verbose_name = "Calendario Guardado"
        verbose_name_plural = "Calendarios Guardados"
        ordering = ['-fecha_creacion']  # El más reciente primero

    def __str__(self):
        return f"{self.nombre} ({self.fecha_creacion.strftime('%d/%m/%Y')})"



# ─────────────────────────────────────────────
# Evidencia
# Archivos que el alumno sube para un Seminario.
# ─────────────────────────────────────────────
def evidencia_upload_path(instance, filename):
    """Guarda en: evidencias/<alumno_id>/<seminario_id>/<filename>"""
    return os.path.join(
        'evidencias',
        str(instance.seminario.alumno_id),
        str(instance.seminario_id),
        filename,
    )


class Evidencia(models.Model):
    TIPO_CHOICES = [
        ('imagen', 'Imagen'),
        ('pdf', 'PDF'),
        ('otro', 'Otro'),
    ]

    seminario = models.ForeignKey(
        'Seminario', on_delete=models.CASCADE, related_name='evidencias')
    archivo = models.FileField(upload_to=evidencia_upload_path)
    tipo = models.CharField(
        max_length=10, choices=TIPO_CHOICES, default='otro')
    nombre = models.CharField(max_length=200, blank=True)
    subido_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['subido_en']

    def save(self, *args, **kwargs):
        # Determina el tipo automáticamente por extensión
        if self.archivo:
            ext = os.path.splitext(self.archivo.name)[1].lower()
            if ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp'):
                self.tipo = 'imagen'
            elif ext == '.pdf':
                self.tipo = 'pdf'
            else:
                self.tipo = 'otro'

            # Usa el nombre del archivo como nombre legible
            # si no se proporcionó
            if not self.nombre:
                self.nombre = os.path.basename(self.archivo.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Evidencia [{self.tipo}] — Seminario {self.seminario_id}"


# ─────────────────────────────────────────────
# SolicitudCambioTutor
# Registro de solicitudes de cambio de tutor.
# ─────────────────────────────────────────────
class SolicitudCambioTutor(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]

    alumno = models.ForeignKey(
        'Alumno', on_delete=models.CASCADE, related_name='solicitudes_tutor')
    motivo = models.TextField()
    estado = models.CharField(
        max_length=10, choices=ESTADO_CHOICES, default='pendiente')
    creada_en = models.DateTimeField(auto_now_add=True)
    resuelta_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-creada_en']

    def __str__(self):
        return f"Solicitud cambio tutor — {self.alumno} ({self.estado})"


class FormularioComite(models.Model):
    ESTADO_CHOICES = [
        ('rechazado', 'Rechazado'),
        ('pendiente', 'Pendiente'),
        ('completo', 'Completo'),
    ]

    seminario = models.OneToOneField(
        'Seminario', on_delete=models.CASCADE,
        related_name='formulario_comite')

    # ── Contenido del informe (sólo el tutor los llena) ──────
    el_comite_encuentra = models.TextField(blank=True)
    observaciones = models.TextField(blank=True)
    dictamen = models.TextField(blank=True)
    propuestas = models.TextField(blank=True)

    # ── Calificaciones individuales ───────────────────────────
    calificacion_tutor = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True)
    calificacion_miembro1 = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True)
    calificacion_miembro2 = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True)

    # ── Firmas (True = firmado/aprobado) ──────────────────────
    firma_tutor = models.BooleanField(default=False)
    firma_miembro1 = models.BooleanField(default=False)
    firma_miembro2 = models.BooleanField(default=False)

    # ── Calculados automáticamente ────────────────────────────
    calificacion_final = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True)
    estado_general = models.CharField(
        max_length=15, choices=ESTADO_CHOICES, default='pendiente')

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Formulario de Comité'

    # ── Helpers ───────────────────────────────────────────────

    @property
    def todos_firmaron(self):
        return self.firma_tutor and self.firma_miembro1 and self.firma_miembro2

    def calcular_calificacion_final(self):
        califs = [
            c for c in (
                self.calificacion_tutor,
                self.calificacion_miembro1,
                self.calificacion_miembro2,
            ) if c is not None
        ]
        if not califs:
            return None
        promedio = sum(califs) / Decimal(len(califs))
        return promedio.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def generar_y_guardar_pdf(self):
        """
        Genera el PDF del informe del comité usando utils_pdf_comite
        y lo guarda en el campo actaComite del Seminario asociado.
        """
        from .utils_pdf_comite import generar_pdf_comite

        try:
            # Generar el PDF en bytes
            pdf_bytes = generar_pdf_comite(self)

            # Crear nombre del archivo
            sem_num = self.seminario.numero
            periodo = self.seminario.periodo
            alumno_nombre = self.seminario.alumno.nombre.replace(' ', '_')
            filename = (
                f"acta_comite_sem{sem_num}_p{periodo}_{alumno_nombre}_"
                f"{self.seminario.alumno.id}.pdf"
            )
            # Eliminar el archivo anterior si existe
            if self.seminario.actaComite:
                self.seminario.actaComite.delete(save=False)

            # Guardar el PDF en el campo actaComite del seminario
            self.seminario.actaComite.save(
                filename, ContentFile(pdf_bytes), save=False)
            self.seminario.save(update_fields=['actaComite'])

            return True

        except Exception as e:
            # Loggear el error si es necesario
            print(
                f"Error generando PDF para seminario {self.seminario_id}: {str(e)}")
            return False

    def save(self, *args, **kwargs):
        # Guardar el estado anterior para detectar cambios en las firmas
        if self.pk:
            try:
                old_instance = FormularioComite.objects.get(pk=self.pk)
                old_firmas = (
                    old_instance.firma_tutor,
                    old_instance.firma_miembro1,
                    old_instance.firma_miembro2,
                )
                new_firmas = (
                    self.firma_tutor,
                    self.firma_miembro1,
                    self.firma_miembro2,
                )
                firmas_cambiaron = old_firmas != new_firmas
            except FormularioComite.DoesNotExist:
                firmas_cambiaron = True
        else:
            firmas_cambiaron = True

        # 1. Calcular calificaciones y estado del formulario
        self.calificacion_final = self.calcular_calificacion_final()

        estaba_completo = (
            self.estado_general == "completo"
            if self.pk
            else False
        )

        self.estado_general = (
            "completo"
            if self.todos_firmaron
            else "pendiente"
        )

        # Detectar si ACABAMOS de completar el formulario
        se_completo_ahora = (
            not estaba_completo
            and self.estado_general == "completo"
        )

        # 2. Ejecutar el guardado del formulario en la base de datos
        super().save(*args, **kwargs)

        # 3. Sincronizar calificación en el Seminario asociado
        if self.calificacion_final is not None:
            self.seminario.__class__.objects.filter(
                pk=self.seminario_id,
            ).update(
                calificacion=self.calificacion_final,
            )

        # 4. Generar el PDF si:
        #    a) Acabamos de completar el formulario
        #    b) Ya estaba completo pero cambiaron las firmas
        #    c) No existe el actaComite y ya está completo
        if (
            se_completo_ahora
            or (
                self.estado_general == "completo"
                and not self.seminario.actaComite
            )
            or (
                self.estado_general == "completo"
                and firmas_cambiaron
            )
        ):
            # Generar y guardar el PDF en el seminario
            self.generar_y_guardar_pdf()

        # 5. LÓGICA DE PROMOCIÓN:
        # Solo si está completo y tiene calificación suficiente
        if (
            self.estado_general == "completo"
            and self.calificacion_final is not None
            and self.calificacion_final >= Decimal("6.00")
        ):
            alumno = self.seminario.alumno

            # Convertir semestre a entero para comparación
            try:
                semestre_actual = (
                    int(alumno.semestre)
                    if alumno.semestre
                    else 0
                )
            except ValueError:
                semestre_actual = 0

            # Control de Idempotencia
            if semestre_actual == self.seminario.numero:
                if semestre_actual < 8:
                    nuevo_semestre = semestre_actual + 1

                    # Guardar como string
                    alumno.semestre = str(nuevo_semestre)
                    alumno.save(
                        update_fields=["semestre"],
                    )

    def __str__(self):
        pdf_status = "✓ PDF" if self.seminario.actaComite else "✗ PDF"
        return (
            f"Formulario Comité — Seminario {self.seminario_id} "
            f"({self.estado_general}) {pdf_status}"
        )


class ActaAlumnoData(models.Model):
    """
    Almacena los datos que el alumno llenó para su acta semestral.
    Una vez creado, el formulario queda bloqueado.
    """
    seminario = models.OneToOneField(
        'Seminario',
        on_delete=models.CASCADE,
        related_name='acta_data'
    )

    actividad_principal = models.CharField(max_length=200)
    reuniones_tutor = models.PositiveSmallIntegerField(default=0)
    reuniones_comite = models.PositiveSmallIntegerField(default=0)
    coloquios = models.PositiveSmallIntegerField(default=0)
    cursos = models.TextField(blank=True)
    articulos = models.TextField(blank=True)
    eventos = models.TextField(blank=True)
    plan_siguiente = models.TextField()
    comentarios = models.TextField(blank=True)

    generado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Datos de acta del alumno"

    def __str__(self):
        return f"Acta — {self.seminario}"

    def to_dict(self):
        """Devuelve los datos como dict compatible con generar_acta_alumno."""
        return {
            'actividad_principal': self.actividad_principal,
            'reuniones_tutor': self.reuniones_tutor,
            'reuniones_comite': self.reuniones_comite,
            'coloquios': self.coloquios,
            'cursos': self.cursos,
            'articulos': self.articulos,
            'eventos': self.eventos,
            'plan_siguiente': self.plan_siguiente,
            'comentarios': self.comentarios,
        }
