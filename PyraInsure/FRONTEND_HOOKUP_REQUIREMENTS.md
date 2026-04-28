# PyraInsure Frontend — Backend Hookup Requirements

This document catalogs every UI element from the hifi design system that has no current backend support and will need wiring up before displaying real data. The frontend templates are complete and styled — these are the missing backend features.

---

## Summary

The design handoff has been fully applied to all Django templates. The frontend is ready for data integration. Below are the 15 categories of features that need backend support, prioritized by user impact.

---

## 1. Dashboard: Per-Submission CoveraGap Score (HIGH PRIORITY)

**Where:** `Dashboard` page, "Recent submissions" list — shows a score chip next to each submission
**What's Missing:** The `dashboard()` view returns `IntakeSubmission` objects but does not compute or annotate the CoveraGap score for each
**Backend Work:**
```python
# In apps/agents/views.py, dashboard() view:
from django.db.models import OuterRef, Subquery, Sum
from apps.gap_scoring.models import GapFinding

points_subq = (GapFinding.objects
    .filter(submission=OuterRef('pk'))
    .values('submission')
    .annotate(s=Sum('points'))
    .values('s'))

recent_submissions = submissions.annotate(
    gap_points=Subquery(points_subq)
)

# In template: score = max(0, 100 - sub.gap_points)
# Chip color: good if score >= 75, warn if >= 50, bad if < 50
```
**Effort:** Small — view annotation only
**Blocks:** Dashboard visual, customer submissions list display

---

## 2. Dashboard: "Open Intake Links" Stat Card (HIGH PRIORITY)

**Where:** Dashboard, top stat card row — 4th card shows "Open intake links: 14"
**What's Missing:** No context variable for the count of active, non-expired questionnaire links
**Backend Work:**
```python
# In apps/agents/views.py, dashboard():
open_links_count = QuestionnaireLink.objects.filter(
    agent=agent_profile,
    is_active=True,
    completed_at__isnull=True
).exclude(expires_at__lt=timezone.now()).count()
context['open_links_count'] = open_links_count
```
**Effort:** Small — view query only
**Blocks:** Dashboard stat card

---

## 3. Customer Detail: CoveraGap Score Ring (HIGH PRIORITY)

**Where:** `Customer Detail` page, right sidebar — animated ring shows the customer's score
**What's Missing:** The `customer_detail()` view doesn't compute the latest submission's score
**Backend Work:**
```python
# In apps/customers/views.py, customer_detail():
latest_submitted = submissions.filter(status='submitted').first()
coverage_score = None
if latest_submitted:
    pts = latest_submitted.gapfinding_set.aggregate(total=Sum('points'))['total'] or 0
    coverage_score = max(0, 100 - pts)
context['coverage_score'] = coverage_score
```
**Effort:** Small — view annotation only
**Blocks:** Customer detail ring animation, score display

---

## 4. Customer Detail: Structured Coverage Data (MEDIUM PRIORITY)

**Where:** `Customer Detail` page, "Current coverage" card — shows "BlueCross PPO · Active" rows per member
**What's Missing:** Coverage data is stored as unstructured `IntakeAnswer` rows. No dedicated `CoverageRecord` model
**Short-term Solution:** Look up specific `IntakeAnswer` keys by `question_key` in the template:
```django
{% for member in latest_submission.householdmember_set.all %}
  {% with answers=latest_submission.intakeanswer_set.filter|dictsort:"question_key" %}
    {# Render answers where question_key contains "coverage" for this member #}
  {% endwith %}
{% endfor %}
```
**Long-term Solution:** Add `CoverageRecord` model:
```python
class CoverageRecord(models.Model):
    submission = models.ForeignKey(IntakeSubmission, CASCADE)
    member = models.ForeignKey(HouseholdMember, CASCADE, null=True)
    coverage_type = models.CharField(choices=['health', 'life', 'auto', 'home', 'umbrella'])
    provider_name = models.CharField()
    status = models.CharField(choices=['active', 'inactive', 'pending'])
```
**Effort:** Medium (short-term lookup) / Large (new model + migration)
**Blocks:** Customer detail coverage display

---

## 5. Customer Detail: Activity Timeline (MEDIUM PRIORITY)

**Where:** `Customer Detail` page, "Recent activity" timeline — shows timestamped events (submission received, call scheduled, etc.)
**What's Missing:** No `ActivityEvent` model. Timeline can only show `IntakeSubmission` dates for now
**Backend Work:** Add model:
```python
class ActivityEvent(models.Model):
    customer = models.ForeignKey(CustomerRecord, CASCADE, related_name='events')
    event_type = models.CharField(choices=[
        ('submission_received', 'Intake submitted'),
        ('call_scheduled', 'Call scheduled'),
        ('notes_added', 'Agent notes added'),
        ('referral_sent', 'Referral sent'),
    ])
    occurred_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-occurred_at']
```
Add migration, create events when submissions are created, calls are logged, etc.
**Effort:** Medium — model, migration, event creation in views
**Blocks:** Customer detail timeline display

---

## 6. Pre-call Summary: Structured Talking Points (MEDIUM PRIORITY)

**Where:** `Pre-call Summary` page, "Talking points" card grid — shows articles with "Hook", "Suggested Ask", "Quick Facts"
**What's Missing:** Backend generates `talking_points` as a flat `list[str]`. Template expects structured dicts with `hook`, `ask`, `facts` keys
**Backend Work:** Modify `apps/intake/views.py` `pre_call_summary()` to generate structured points:
```python
talking_points_lookup = {
    'no_health_coverage': {
        'hook': 'This is a critical gap.',
        'ask': 'What would happen if you had an unexpected health emergency?',
        'facts': ['Medical bills are the #1 cause of debt', 'ACA plans start ~$250/mo'],
    },
    # ... more points
}

structured_points = []
for finding in submission.gapfinding_set.all():
    if finding.category == 'health':
        point_key = derive_key_from_finding(finding)
        if point_key in talking_points_lookup:
            structured_points.append(talking_points_lookup[point_key])

context['talking_points'] = structured_points
```
**Effort:** Medium — view logic + lookup table
**Blocks:** Pre-call summary talking points display

---

## 7. Pre-call Summary: "Don't Bring Up" Private Context (MEDIUM PRIORITY)

**Where:** `Pre-call Summary` page — conditional "Don't bring up: Recent layoff" box
**What's Missing:** No `private_notes` field on `IntakeSubmission`. No intake question to capture private context
**Backend Work:**
1. Add field: `private_notes = models.TextField(blank=True)` to `IntakeSubmission`
2. Add migration: `python manage.py makemigrations && migrate`
3. Add intake question: Step with optional "Is there anything you'd prefer we don't discuss?" input
4. Store answer: `submission.private_notes = request.POST.get('private_notes', '')`
**Effort:** Medium — model field, migration, form question, template conditional
**Blocks:** Pre-call summary "don't bring up" box

---

## 8. Create Intake Link: Client Selection Step 1 (MEDIUM PRIORITY)

**Where:** `Create Link` wizard, Step 1 "Client" — agent selects/creates the client for the intake
**What's Missing:** `QuestionnaireLink` has no `customer` FK. No client search endpoint
**Backend Work:**
1. Add field to model:
   ```python
   class QuestionnaireLink(models.Model):
       customer = models.ForeignKey(CustomerRecord, null=True, blank=True, on_delete=models.SET_NULL)
   ```
2. Add migration
3. Create search endpoint:
   ```python
   # apps/customers/views.py
   def customer_search(request):
       q = request.GET.get('q', '')
       customers = CustomerRecord.objects.filter(
           agent=request.user.agentprofile
       ).filter(
           Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q)
       )[:10]
       return JsonResponse([{
           'id': c.id, 'name': f'{c.first_name} {c.last_name}', 'email': c.email
       } for c in customers])
   
   # Add to urls.py: path('customers/search/', customer_search, name='customer_search')
   ```
4. Add JS autocomplete in template (simple fetch + list render)
**Effort:** Medium — model field, migration, endpoint, JS integration
**Blocks:** Create link step 1 functionality

---

## 9. Create Intake Link: Expiration & Reminder Fields (MEDIUM PRIORITY)

**Where:** `Create Link` wizard, Step 2 "Customize" — "Expires in: 7 days", "Remind after: 48 hours"
**What's Missing:** `QuestionnaireLink.expires_at` exists but not exposed in form. No `reminder_after_hours` field
**Backend Work:**
1. Add field:
   ```python
   class QuestionnaireLink(models.Model):
       reminder_after_hours = models.IntegerField(null=True, blank=True)
   ```
2. Add migration
3. Update `QuestionnaireLinkCreateForm` to expose both fields:
   ```python
   class QuestionnaireLinkCreateForm(forms.ModelForm):
       expires_in_days = forms.ChoiceField(choices=[(3, '3 days'), (7, '7 days'), (14, '14 days')])
       reminder_after_hours = forms.ChoiceField(choices=[(24, '24 hours'), (48, '48 hours')], required=False)
   ```
4. In view, compute `expires_at`:
   ```python
   if form.is_valid():
       link = form.save(commit=False)
       link.expires_at = timezone.now() + timedelta(days=int(form.cleaned_data['expires_in_days']))
       link.save()
   ```
**Effort:** Small — model field, migration, form, view logic
**Blocks:** Create link step 2 UI

---

## 10. Create Intake Link: Custom Agent Greeting (SMALL PRIORITY)

**Where:** `Create Link` wizard, Step 2 "Customize" — text input "Greeting from you"
**What's Missing:** No `agent_greeting` field on `QuestionnaireLink`
**Backend Work:**
1. Add field: `agent_greeting = models.TextField(blank=True)`
2. Add migration
3. Expose in form: `fields = [..., 'agent_greeting']`
4. Render in intake welcome: `{{ questionnaire_link.agent_greeting }}`
**Effort:** Small — field, migration, form, template
**Blocks:** Create link step 2 custom greeting

---

## 11. Public Score Page: "See Jane's Call Notes" CTA (SMALL PRIORITY)

**Where:** `CoveraGap Score` public page — "See Jane's call notes" button to pre-call summary
**What's Missing:** Score page is public (no auth), but pre-call summary is login-required. Client gets 302 to login
**Backend Work:** Option 1 — Make pre-call summary viewable with score token:
```python
# In apps/intake/views.py, pre_call_summary():
submission = IntakeSubmission.objects.get(score_access_token=score_token)
# ... render summary without login required

# In urls.py: path('summaries/<score_token>/', pre_call_summary_public)
```
OR Option 2 — Hide CTA if no agent:
```django
{% if submission.agent %}
  <a class="btn brand" href="{% url 'pre_call_summary' submission.id %}">See call notes →</a>
{% endif %}
```
**Effort:** Small — view logic OR template conditional
**Blocks:** Public score page CTA

---

## 12. Public Score Page: "Send Myself a Copy" Button (LARGE PRIORITY)

**Where:** `CoveraGap Score` page — button to email the score to client
**What's Missing:** No email backend configured, no `send_score_email` view
**Backend Work:**
1. Configure email backend in `settings.py`:
   ```python
   EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # dev
   # or:
   EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
   EMAIL_HOST = os.getenv('EMAIL_HOST')
   EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
   EMAIL_USE_TLS = True
   EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
   EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
   ```
2. Create view:
   ```python
   def send_score_email(request, score_token):
       submission = IntakeSubmission.objects.get(score_access_token=score_token)
       score = max(0, 100 - submission.gapfinding_set.aggregate(Sum('points'))['points__sum'] or 0)
       send_mail(
           'Your CoveraGap Score',
           render_to_string('emails/score.txt', {'submission': submission, 'score': score}),
           settings.DEFAULT_FROM_EMAIL,
           [request.POST.get('email')],
       )
       return JsonResponse({'sent': True})
   ```
3. Add endpoint in urls, call via AJAX from template
**Effort:** Large — email config, view, email template, JS integration
**Blocks:** Score email functionality

---

## 13. Referral Management UI (MEDIUM PRIORITY)

**Where:** `Pre-call Summary` page — referral opportunities section (currently data only)
**What's Missing:** `ReferralOpportunity` model exists with status workflow, but no views/templates to manage status
**Backend Work:**
1. Create views:
   ```python
   # List referrals for pre-call
   # Update referral status (possible → ready → referred → closed)
   ```
2. Create templates: referral list card, status update buttons
3. Add URLs
4. Integrate into pre-call summary template
**Effort:** Medium — views, templates, status transitions
**Blocks:** Pre-call summary referral management

---

## 14. Customer List Page (SMALL PRIORITY)

**Where:** Sidebar nav "Customers" link — currently no `/customers/` index route, only detail pages exist
**What's Missing:** No `customers_list` view or URL
**Backend Work:**
```python
# In apps/customers/views.py:
def customers_list(request):
    agent = request.user.agentprofile
    customers = CustomerRecord.objects.filter(agent=agent).order_by('-updated_at')
    return render(request, 'customers/list.html', {'customers': customers})

# In urls.py: path('customers/', customers_list, name='customers_list')
# Create template: templates/customers/list.html
```
**Effort:** Small — view, template, URL
**Blocks:** Sidebar "Customers" nav link

---

## 15. Link Management: Deactivation UI (SMALL PRIORITY)

**Where:** Dashboard links table — button to deactivate a link (disable further intakes)
**What's Missing:** `QuestionnaireLink.is_active` field exists but no UI to toggle it
**Backend Work:**
```python
# View to toggle:
def toggle_link_active(request, link_id):
    link = QuestionnaireLink.objects.get(id=link_id, agent=request.user.agentprofile)
    link.is_active = not link.is_active
    link.save()
    return JsonResponse({'is_active': link.is_active})

# Template button (in dashboard links table):
<button class="btn sm ghost copy-btn" data-toggle-link="{{ link.id }}">
  {% if link.is_active %}Deactivate{% else %}Activate{% endif %}
</button>
```
**Effort:** Small — view, JS, template button
**Blocks:** Link management UI

---

## Not Blocked (Frontend Complete)

These features are fully working on the frontend with existing backend support:

- ✅ Login/logout (Django auth)
- ✅ Dashboard stat cards (view provides stats)
- ✅ Recent intakes table (view provides recent_links)
- ✅ Create intake link form (view + form exist)
- ✅ Link created success page (view exists)
- ✅ Intake wizard (all steps working with forms)
- ✅ Household member CRUD (views exist)
- ✅ Drug autocomplete (RxTerms endpoint working)
- ✅ Prescription entry (form working)
- ✅ Score display (view computes scores)
- ✅ Animated ring/confetti (JS animations ready)

---

## Implementation Priority

**Week 1 (High Impact):**
1. Dashboard per-submission score (blocks visual completeness)
2. Customer detail ring score (blocks visual completeness)
3. Open links stat card (completes dashboard stats)

**Week 2 (Feature Parity):**
4. Create link client selection (feature completeness)
5. Expiration + reminder fields (feature completeness)
6. Talking points structure (visual completeness on pre-call)
7. Private context field (visual completeness on pre-call)

**Week 3 (Polish):**
8. Activity timeline model (customer detail enrichment)
9. Referral management UI (pre-call completeness)
10. Email send (score page feature)

**Deferred (Nice to Have):**
- Customer list page
- Link deactivation UI
- Custom greeting field

---

## Testing Checklist

After implementing each feature, verify:
- [ ] Data flows from backend to template
- [ ] No 500 errors or missing context variables
- [ ] Styling matches hifi design system
- [ ] Mobile responsive (85% of features appear on intake mobile views)
- [ ] Animations trigger correctly (ring, confetti on score page)
