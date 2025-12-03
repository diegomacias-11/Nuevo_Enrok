from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Cita",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("prospecto", models.CharField(max_length=150)),
                ("giro", models.CharField(blank=True, max_length=150, null=True)),
                (
                    "tipo",
                    models.CharField(
                        blank=True,
                        choices=[("Producto", "Producto"), ("Servicio", "Servicio")],
                        max_length=50,
                        null=True,
                    ),
                ),
                (
                    "medio",
                    models.CharField(
                        choices=[
                            ("Apollo", "Apollo"),
                            ("Remarketing", "Remarketing"),
                            ("Alianzas", "Alianzas"),
                            ("Lead", "Lead"),
                            ("Procompite", "Procompite"),
                            ("Ejecutivos", "Ejecutivos"),
                            ("Personales", "Personales"),
                            ("Expos / Eventos Deportivos", "Expos / Eventos Deportivos"),
                        ],
                        max_length=100,
                    ),
                ),
                (
                    "servicio",
                    models.CharField(
                        choices=[
                            ("Pendiente", "Pendiente"),
                            ("Auditoría Contable", "Auditoría Contable"),
                            ("Contabilidad", "Contabilidad"),
                            ("Corridas", "Corridas"),
                            ("E-Commerce", "E-Commerce"),
                            ("Laboral", "Laboral"),
                            ("Maquila de Nómina", "Maquila de Nómina"),
                            ("Marketing", "Marketing"),
                            ("Reclutamiento", "Reclutamiento"),
                            ("REPSE", "REPSE"),
                        ],
                        max_length=100,
                    ),
                ),
                (
                    "servicio2",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("Pendiente", "Pendiente"),
                            ("Auditoría Contable", "Auditoría Contable"),
                            ("Contabilidad", "Contabilidad"),
                            ("Corridas", "Corridas"),
                            ("E-Commerce", "E-Commerce"),
                            ("Laboral", "Laboral"),
                            ("Maquila de Nómina", "Maquila de Nómina"),
                            ("Marketing", "Marketing"),
                            ("Reclutamiento", "Reclutamiento"),
                            ("REPSE", "REPSE"),
                        ],
                        max_length=100,
                        null=True,
                    ),
                ),
                (
                    "servicio3",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("Pendiente", "Pendiente"),
                            ("Auditoría Contable", "Auditoría Contable"),
                            ("Contabilidad", "Contabilidad"),
                            ("Corridas", "Corridas"),
                            ("E-Commerce", "E-Commerce"),
                            ("Laboral", "Laboral"),
                            ("Maquila de Nómina", "Maquila de Nómina"),
                            ("Marketing", "Marketing"),
                            ("Reclutamiento", "Reclutamiento"),
                            ("REPSE", "REPSE"),
                        ],
                        max_length=100,
                        null=True,
                    ),
                ),
                ("contacto", models.CharField(blank=True, max_length=150, null=True)),
                (
                    "telefono",
                    models.CharField(
                        blank=True,
                        max_length=10,
                        null=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                "^\\d{10}$", "El teléfono debe tener exactamente 10 dígitos."
                            )
                        ],
                    ),
                ),
                ("correo", models.EmailField(blank=True, max_length=254, null=True, verbose_name="Correo")),
                ("conexion", models.CharField(blank=True, max_length=150, null=True)),
                ("vendedor", models.CharField(choices=[("Giovanni", "Giovanni"), ("Daniel S.", "Daniel S.")], max_length=50)),
                (
                    "estatus_cita",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("Agendada", "Agendada"),
                            ("Pospuesta", "Pospuesta"),
                            ("Cancelada", "Cancelada"),
                            ("Atendida", "Atendida"),
                        ],
                        max_length=50,
                        null=True,
                    ),
                ),
                (
                    "numero_cita",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("Primera", "Primera"),
                            ("Segunda", "Segunda"),
                            ("Tercera", "Tercera"),
                            ("Cuarta", "Cuarta"),
                            ("Quinta", "Quinta"),
                        ],
                        max_length=10,
                        null=True,
                    ),
                ),
                (
                    "estatus_seguimiento",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("Esperando respuesta del cliente", "Esperando respuesta del cliente"),
                            ("Agendar nueva cita", "Agendar nueva cita"),
                            ("Solicitud de propuesta", "Solicitud de propuesta"),
                            ("Elaboración de propuesta", "Elaboración de propuesta"),
                            ("Propuesta enviada", "Propuesta enviada"),
                            ("Se envió auditoría Laboral", "Se envió auditoría Laboral"),
                            ("Stand by", "Stand by"),
                            ("Pendiente de cierre", "Pendiente de cierre"),
                            ("En activación", "En activación"),
                            ("Reclutando", "Reclutando"),
                            ("Cerrado", "Cerrado"),
                            ("No está interesado en este servicio", "No está interesado en este servicio"),
                            ("Fuera de su presupuesto", "Fuera de su presupuesto"),
                        ],
                        max_length=100,
                        null=True,
                    ),
                ),
                ("comentarios", models.TextField(blank=True, null=True)),
                (
                    "lugar",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("Oficina de Arau", "Oficina de Arau"),
                            ("Oficina del cliente", "Oficina del cliente"),
                            ("Zoom", "Zoom"),
                        ],
                        max_length=50,
                        null=True,
                    ),
                ),
                ("fecha_cita", models.DateTimeField()),
                ("fecha_registro", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Cita",
                "verbose_name_plural": "Citas",
                "ordering": ["-fecha_cita"],
            },
        ),
    ]
