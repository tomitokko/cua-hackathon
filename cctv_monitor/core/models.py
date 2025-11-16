from django.db import models


class MonitoringSession(models.Model):
	class Status(models.TextChoices):
		PENDING = "pending", "Pending"
		RUNNING = "running", "Running"
		COMPLETED = "completed", "Completed"
		ERROR = "error", "Error"

	youtube_url = models.URLField()
	goal = models.CharField(max_length=255)
	stream_url = models.TextField(blank=True)
	status = models.CharField(
		max_length=20, choices=Status.choices, default=Status.PENDING
	)
	event_detected = models.BooleanField(default=False)
	last_frame_number = models.PositiveIntegerField(default=0)
	output_folder = models.CharField(max_length=500, blank=True)
	error_message = models.TextField(blank=True)
	started_at = models.DateTimeField(null=True, blank=True)
	finished_at = models.DateTimeField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self) -> str:
		return f"MonitoringSession #{self.pk}"


class MonitoringLog(models.Model):
	session = models.ForeignKey(
		MonitoringSession, related_name="logs", on_delete=models.CASCADE
	)
	frame_number = models.PositiveIntegerField(null=True, blank=True)
	message = models.TextField()
	is_alert = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["id"]

	def __str__(self) -> str:
		prefix = "Alert" if self.is_alert else "Log"
		return f"{prefix} #{self.pk} for session {self.session_id}"
