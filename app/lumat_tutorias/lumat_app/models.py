import os
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Alumno(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    matricula = models.CharField(
        max_length=8, unique=True, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100)
    semestre = models.CharField(max_length=50)
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
    fecha = models.DateField()
    hora = models.TimeField()
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
# Agregar estos modelos a tu models.py existente
# (los modelos anteriores: Alumno, Docente, Comite, Seminario,
# CalifSeminario quedan igual)


# ─────────────────────────────────────────────
# SeminarioNumero
# Vincula un Seminario con su número (1-8) para
# un alumno. Un alumno solo puede tener un
# seminario por número.
# # ─────────────────────────────────────────────
# class SeminarioNumero(models.Model):
#     alumno = models.ForeignKey(
#         'Alumno',
#         on_delete=models.CASCADE,
#         related_name='seminarios_numerados'
#     )
#     seminario = models.OneToOneField(
#         'Seminario',
#         on_delete=models.CASCADE,
#         related_name='numero_obj',
#         null=True,
#         blank=True
#     )
#     numero = models.PositiveSmallIntegerField()  # 1 – 8

#     class Meta:
#         unique_together = ('alumno', 'numero')
#         ordering = ['numero']

#     def __str__(self):
#         return f"Seminario {self.numero} — {self.alumno}"


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
