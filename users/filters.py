from .models import JobApplication


def filter_applications(queryset, params):
    status_filter = params.get('status')
    label_color_filter = params.get('label_color')
    company_filter = params.get('company')
    title_filter = params.get('title')
    date_applied_from = params.get('date_applied_from')
    date_applied_to = params.get('date_applied_to')

    if status_filter:
        allowed_statuses = [choice[0] for choice in JobApplication.Status.choices]
        if status_filter not in allowed_statuses:
            return None, 'Invalid status'
        queryset = queryset.filter(status=status_filter)

    if label_color_filter:
        allowed_colors = [choice[0] for choice in JobApplication.LabelColor.choices]
        if label_color_filter not in allowed_colors:
            return None, 'Invalid label color'
        queryset = queryset.filter(label_color=label_color_filter)

    if company_filter:
        queryset = queryset.filter(company__icontains=company_filter)

    if title_filter:
        queryset = queryset.filter(title__icontains=title_filter)

    if date_applied_from:
        queryset = queryset.filter(date_applied__gte=date_applied_from)

    if date_applied_to:
        queryset = queryset.filter(date_applied__lte=date_applied_to)

    return queryset, None