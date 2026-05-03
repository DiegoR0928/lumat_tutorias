from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class Alumno(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    matricula = models.CharField(max_length=8, unique=True, null=True, blank=True)
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
    miembro1 = models.ForeignKey(Docente, on_delete=models.CASCADE, related_name='miembro1')
    miembro2 = models.ForeignKey(Docente, on_delete=models.CASCADE, related_name='miembro2')

    def clean(self):
        docentes = [self.tutor_id, self.miembro1_id, self.miembro2_id]
        if len(set(docentes)) != 3:
            raise ValidationError("Los tres docentes del comité deben ser distintos.")

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
    calificacion = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    actaComite = models.FileField(upload_to='actas/', null=True, blank=True)
    actaAlumno = models.FileField(upload_to='actas_alumno/', null=True, blank=True)

    def __str__(self):
        return f"Seminario de {self.alumno.__str__()} - {self.fecha}"
    
class CalifSeminario(models.Model):
    seminario = models.ForeignKey(Seminario, on_delete=models.CASCADE)
    docente = models.ForeignKey(Docente, on_delete=models.CASCADE)
    calificacion = models.DecimalField(max_digits=4, decimal_places=2)

    def __str__(self):
        return f"Calificación de {self.docente.__str__()} para {self.seminario.__str__()}"
    
