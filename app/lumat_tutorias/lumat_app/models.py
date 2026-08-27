import os
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from decimal import Decimal, ROUND_HALF_UP
from django.core.files.base import ContentFile
from django.core.validators import FileExtensionValidator


class Alumno(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    matricula = models.CharField(
        max_length=8, unique=True, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100)
    semestre = models.CharField(max_length=50, default=1)
    correo = models.EmailField()
    posgrado = models.CharField(max_length=50, choices=[('maestria', 'Maestría'), ('doctorado', 'Doctorado')])
    periodo_inicio_estudios = models.CharField(max_length=50)
    periodo_fin_estudios = models.CharField(max_length=50)
    acta_examen_titulacion = models.FileField(upload_to='actas_examen_titulacion/', blank=True, null=True
                                               , validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
                                                  verbose_name="Acta de Examen de Titulación")
    linea_investigacion = models.CharField(max_length=100, choices=[('Materia condensada y energía', 'Materia condensada y energía'), ('Óptica y fotónica', 'Óptica y fotónica'), ('Agua y su manejo sostenible', 'Agua y su manejo sostenible')])
    nacionalidad = models.CharField(max_length=50)
    posgrado_o_universidad_anterior = models.CharField(max_length=100)
    proyecto_investigacion = models.CharField(max_length=200)
    estado = models.CharField(max_length=50, choices=[('activo', 'Activo'), ('egresado', 'Egresado'), ('dado de baja', 'Dado de baja'), ('baja temporal', 'Baja Temporal')], default='activo')

    perfil_completado = models.BooleanField(default=False)

    tesis_pdf = models.FileField(
        upload_to='tesis_alumnos/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        verbose_name="Documento de Tesis (PDF)"
    )

    @property
    def semestre_final_plan(self):
        """Retorna el último semestre ordinario: 4 para Maestría, 8 para Doctorado."""
        return 4 if self.posgrado == 'maestria' else 8

    @property
    def es_ultimo_semestre(self):
        """Indica si el alumno está cursando su último semestre regular o posterior (prórroga)."""
        semestre_actual = int(self.semestre or 1)
        return semestre_actual >= self.semestre_final_plan

    @property
    def total_seminarios_visibles(self):
        """
        Determina cuántos seminarios mostrar en la barra lateral.
        - Maestría: 4 base (hasta 8 con prórroga).
        - Doctorado: 8 base (hasta 14 con prórroga).
        """
        semestre_actual = int(self.semestre or 1)

        if self.posgrado == 'maestria':
            limite_maximo = 8   # 4 base + 4 prórroga
            limite_base = 4
        else:  # 'doctorado'
            limite_maximo = 14  # 8 base + 6 prórroga
            limite_base = 8

        # Muestra los base, pero si va retrasado/avanzado, se expande hasta su semestre actual (con tope máximo)
        total = max(limite_base, semestre_actual)
        return min(total, limite_maximo)

    @property
    def lista_seminarios(self):
        """Devuelve una lista iterable tipo [1, 2, 3, 4...]"""
        return list(range(1, self.total_seminarios_visibles + 1))
    
    def __str__(self):
        return f"{self.nombre} {self.apellido_paterno} ({self.matricula})"


class RetribucionSocial(models.Model):
    alumno = models.ForeignKey(
        'Alumno', 
        on_delete=models.CASCADE, 
        related_name='retribuciones_sociales',
        verbose_name="Estudiante"
    )
    archivo = models.FileField(
        upload_to='retribucion_social/', 
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        verbose_name="Archivo PDF"
    )
    descripcion = models.CharField(
        max_length=200, 
        blank=True, 
        verbose_name="Descripción del documento"
    )
    subido_en = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Fecha de carga"
    )

    class Meta:
        verbose_name = "Retribución Social"
        verbose_name_plural = "Retribuciones Sociales"
        ordering = ['-subido_en']

    def __str__(self):
        return f"Retribución - {self.alumno.matricula} ({self.subido_en.strftime('%Y-%m-%d')})"

class Docente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100)
    correo = models.EmailField()
    firma = models.ImageField(upload_to='firmas/', )
    telefono = models.CharField(max_length=20)
    red_social_investigacion = models.URLField(max_length=200)
    ultimo_grado_estudio = models.CharField(max_length=100)
    universidad_o_centro = models.CharField(max_length=100)
    facultad_o_instituto = models.CharField(max_length=100)
    nombramiento_sni = models.FileField(upload_to='nombramientos_sni/', blank=True, null=True
                                         , validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
                                         verbose_name="Nombramiento SNI")

    def __str__(self):
        return f"{self.nombre} {self.apellido_paterno}"


class Comite(models.Model):
    tutor = models.ForeignKey(Docente, on_delete=models.CASCADE)
    director = models.ForeignKey(
        Docente,
        on_delete=models.CASCADE,
        related_name="director",
        verbose_name="director de tesis",
    )
    coodirector = models.ForeignKey(
        Docente,
        on_delete=models.CASCADE,
        related_name="coodirector",
        verbose_name="coodirector de tesis",
    )
    asesor = models.ForeignKey(
        Docente,
        on_delete=models.CASCADE,
        related_name="asesor",
        verbose_name="asesor de tesis",
    )

    def clean(self):
        docentes = [self.tutor_id, self.director_id, self.coodirector_id, self.asesor_id]
        if len(set(docentes)) != 4:
            raise ValidationError(
                "Los cuatro docentes del comité deben ser distintos.")

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

    class Meta:
        ordering = ['numero']

        constraints = [
            models.UniqueConstraint(
                fields=['alumno', 'numero'],
                name='unique_seminario_periodo'
            )
        ]

    def __str__(self):
        return (
            f"Seminario"
            f"{self.alumno}"
        )


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
        constraints = [
            # A nivel de BD: nunca puede haber dos evidencias
            # para el mismo seminario, sin importar qué vista las cree.
            models.UniqueConstraint(
                fields=['seminario'],
                name='evidencia_unica_por_seminario',
            ),
        ]

    def save(self, *args, **kwargs):
        if self.archivo:
            ext = os.path.splitext(self.archivo.name)[1].lower()
            if ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp'):
                self.tipo = 'imagen'
            elif ext == '.pdf':
                self.tipo = 'pdf'
            else:
                self.tipo = 'otro'

            if not self.nombre:
                self.nombre = os.path.basename(self.archivo.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Evidencia [{self.tipo}] — Seminario {self.seminario_id}"

# ─────────────────────────────────────────────
# ProyectoInvestigacion
# PDF que el alumno sube durante su primer semestre.
# Un solo documento por alumno (se reemplaza si sube uno nuevo).
# ─────────────────────────────────────────────
def proyecto_investigacion_upload_path(instance, filename):
    """Guarda en: proyectos_investigacion/<alumno_id>/<filename>"""
    return os.path.join(
        'proyectos_investigacion',
        str(instance.alumno_id),
        filename,
    )


class ProyectoInvestigacion(models.Model):
    alumno = models.OneToOneField(
        'Alumno',
        on_delete=models.CASCADE,
        related_name='proyecto_investigacion_doc',
    )
    archivo = models.FileField(upload_to=proyecto_investigacion_upload_path)
    nombre_archivo = models.CharField(max_length=200, blank=True)
    subido_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Proyecto de investigación"
        verbose_name_plural = "Proyectos de investigación"

    def save(self, *args, **kwargs):
        if self.archivo and not self.nombre_archivo:
            self.nombre_archivo = os.path.basename(self.archivo.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Proyecto de investigación — {self.alumno}"

    
class SolicitudCambioComite(models.Model):
    ROLES = [
        ('tutor',       'Tutor'),
        ('director',    'Director de tesis'),
        ('coodirector', 'Coodirector de tesis'),
        ('asesor',      'Asesor de tesis'),
    ]
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('aceptada',  'Aceptada'),
        ('rechazada', 'Rechazada'),
    ]

    alumno         = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name='solicitudes_cambio_comite')
    rol_solicitado = models.CharField(max_length=20, choices=ROLES)
    motivo         = models.TextField()
    estado         = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    respuesta_admin = models.TextField(blank=True)

    class Meta:
        ordering = ['-fecha_solicitud']

    def __str__(self):
        return f"Solicitud de {self.alumno} — {self.get_rol_solicitado_display()} ({self.estado})"


# models.py
from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from django.core.files.base import ContentFile

class FormularioComite(models.Model):
    ESTADO_CHOICES = [
        ('rechazado', 'Rechazado'),
        ('pendiente', 'Pendiente'),
        ('completo', 'Completo'),
    ]

    DICTAMEN_CHOICES = [
        ('aprobado', 'Aprobado'),
        ('reprobado', 'Reprobado'),
    ]

    seminario = models.OneToOneField(
        'Seminario', on_delete=models.CASCADE,
        related_name='formulario_comite')

    # ── Dictamen y Evaluación ─────────────────────────────────
    dictamen = models.CharField(
        max_length=15, choices=DICTAMEN_CHOICES, default='aprobado')
    
    el_comite_encuentra = models.TextField(blank=True)
    observaciones = models.TextField(blank=True)

    # ── Plan de Trabajo ───────────────────────────────────────
    # True = Ratifica el plan propuesto por el alumno en ActaAlumnoData
    # False = El comité hace modificaciones
    ratifica_plan = models.BooleanField(default=True)
    propuestas = models.TextField(blank=True, verbose_name="Modificaciones al plan de trabajo")

    # ── Calificaciones individuales ───────────────────────────
    calificacion_tutor = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True)
    calificacion_director = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True)
    calificacion_coodirector = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True)
    calificacion_asesor = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True)

    # ── Firmas (True = firmado/aprobado) ──────────────────────
    firma_tutor = models.BooleanField(default=False)
    firma_director = models.BooleanField(default=False)
    firma_coodirector = models.BooleanField(default=False)
    firma_asesor = models.BooleanField(default=False)

    # ── Calculados automáticamente ────────────────────────────
    calificacion_final = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True)
    estado_general = models.CharField(
        max_length=15, choices=ESTADO_CHOICES, default='pendiente')

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Formulario de Comité'

    @property
    def todos_firmaron(self):
        return self.firma_tutor and self.firma_director and self.firma_coodirector and self.firma_asesor

    def obtener_plan_trabajo_efectivo(self):
        """Retorna el plan de trabajo final resuelto según la decisión del comité."""
        if self.dictamen == 'reprobado':
            return "No aplica (No Aprobado)"
        if self.ratifica_plan:
            try:
                if hasattr(self.seminario, 'acta_data') and self.seminario.acta_data:
                    return self.seminario.acta_data.plan_siguiente or "Plan de trabajo ratificado."
            except Exception:
                pass
            return "Plan de trabajo propuesto por el alumno ratificado."
        return self.propuestas or "Sin modificaciones especificadas."

    def calcular_calificacion_final(self):
        califs = [
            c for c in (
                self.calificacion_tutor,
                self.calificacion_director,
                self.calificacion_coodirector,
                self.calificacion_asesor,
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
            # periodo = self.seminario.periodo
            alumno_nombre = self.seminario.alumno.nombre.replace(' ', '_')
            filename = (
                f"acta_comite_sem{sem_num}_{alumno_nombre}_"
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
        hubo_cambios_evaluacion = False

        if self.pk:
            try:
                old = FormularioComite.objects.get(pk=self.pk)
                
                # 1. Detectar si cambiaron firmas
                firmas_cambiaron = (
                    old.firma_tutor != self.firma_tutor or
                    old.firma_director != self.firma_director or
                    old.firma_coodirector != self.firma_coodirector or
                    old.firma_asesor != self.firma_asesor
                )
                
                # 2. Detectar si cambiaron las notas individuales o el dictamen
                califs_cambiaron = (
                    old.calificacion_tutor != self.calificacion_tutor or
                    old.calificacion_director != self.calificacion_director or
                    old.calificacion_coodirector != self.calificacion_coodirector or
                    old.calificacion_asesor != self.calificacion_asesor or
                    old.dictamen != self.dictamen
                )
                
                hubo_cambios_evaluacion = firmas_cambiaron or califs_cambiaron

            except FormularioComite.DoesNotExist:
                hubo_cambios_evaluacion = True
        else:
            hubo_cambios_evaluacion = True

        # Recalcular calificación final y estado
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

        se_completo_ahora = (
            not estaba_completo
            and self.estado_general == "completo"
        )

        # Guardar cambios en el formulario
        super().save(*args, **kwargs)

        # Sincronizar calificación en el Seminario
        if self.calificacion_final is not None:
            self.seminario.__class__.objects.filter(
                pk=self.seminario_id,
            ).update(
                calificacion=self.calificacion_final,
            )

        # Regenerar el PDF si:
        # a) Se completaron todas las firmas en este momento
        # b) Ya está completo y el PDF no existe
        # c) Ya está completo y se editó alguna firma, nota o dictamen
        if (
            se_completo_ahora
            or (
                self.estado_general == "completo"
                and not self.seminario.actaComite
            )
            or (
                self.estado_general == "completo"
                and hubo_cambios_evaluacion
            )
        ):
            self.generar_y_guardar_pdf()


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

    # Solo director y codirector autorizan el acta del alumno
    firma_director = models.BooleanField(default=False)
    firma_coodirector = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Datos de acta del alumno"

    def __str__(self):
        return f"Acta — {self.seminario}"

    @property
    def firmas_completas(self):
        """True cuando director y codirector ya autorizaron."""
        return self.firma_director and self.firma_coodirector

    def to_dict(self):
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
