from __future__ import annotations

from django.db import models


class Client(models.Model):
    full_name = models.CharField(max_length=255, blank=True)
    dob = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    income = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.full_name or f"Client #{self.pk}"


class HandwrittenNote(models.Model):
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="handwritten_notes",
    )
    uploaded_file = models.FileField(upload_to="handwritten_notes/%Y/%m/%d/")
    original_filename = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.original_filename or f"Handwritten Note #{self.pk}"


class PolicyDocument(models.Model):
    """
    The canonical stored document (always a single viewable file).

    - If user uploads a PDF: file is the original PDF.
    - If user uploads multiple images: file is the merged PDF.
    """

    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="policy_documents",
    )
    file = models.FileField(upload_to="policy_documents/%Y/%m/%d/")
    original_filename = models.CharField(max_length=255, blank=True)
    page_count = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.original_filename or f"Policy #{self.pk}"


class PolicySource(models.Model):
    """
    Preserves original user uploads when a policy is composed from multiple images.
    """

    policy = models.ForeignKey(PolicyDocument, on_delete=models.CASCADE, related_name="sources")
    file = models.FileField(upload_to="policy_documents/sources/%Y/%m/%d/")
    original_filename = models.CharField(max_length=255, blank=True)
    page_number = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["page_number", "id"]

    def __str__(self) -> str:
        return self.original_filename or f"Policy Source #{self.pk}"


class ClientAttachment(models.Model):
    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"

    class DocumentType(models.TextChoices):
        POLICY = "policy", "Policy"
        HANDWRITTEN_NOTE = "handwritten_note", "Handwritten Note"
        OTHER = "other", "Other"

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="attachments")
    document_type = models.CharField(max_length=50, choices=DocumentType.choices, default=DocumentType.OTHER)
    display_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UPLOADED)
    page_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.display_name or f"Attachment #{self.pk}"


class ClientAttachmentPage(models.Model):
    attachment = models.ForeignKey(ClientAttachment, on_delete=models.CASCADE, related_name="pages")
    page_number = models.PositiveIntegerField()
    image = models.ImageField(upload_to="client_attachment_pages/%Y/%m/%d/")
    original_filename = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["page_number", "id"]
        constraints = [
            models.UniqueConstraint(fields=["attachment", "page_number"], name="crm_attachment_unique_page_number")
        ]

    def __str__(self) -> str:
        return f"Attachment {self.attachment_id} - Page {self.page_number}"
