{{/*
Expand the chart name.
*/}}
{{- define "cloudops-sre-platform.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "cloudops-sre-platform.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Chart label.
*/}}
{{- define "cloudops-sre-platform.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Common labels.
*/}}
{{- define "cloudops-sre-platform.labels" -}}
helm.sh/chart: {{ include "cloudops-sre-platform.chart" . }}
app.kubernetes.io/name: {{ include "cloudops-sre-platform.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/*
Selector labels.
*/}}
{{- define "cloudops-sre-platform.selectorLabels" -}}
app.kubernetes.io/name: {{ include "cloudops-sre-platform.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "cloudops-sre-platform.backendServiceName" -}}
{{- default (printf "%s-backend" (include "cloudops-sre-platform.fullname" .)) .Values.backend.service.name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "cloudops-sre-platform.frontendServiceName" -}}
{{- default (printf "%s-frontend" (include "cloudops-sre-platform.fullname" .)) .Values.frontend.service.name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "cloudops-sre-platform.backendServiceAccountName" -}}
{{- if .Values.backend.serviceAccount.create -}}
{{- default (printf "%s-backend" (include "cloudops-sre-platform.fullname" .)) .Values.backend.serviceAccount.name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- default "default" .Values.backend.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{- define "cloudops-sre-platform.databaseSecretName" -}}
{{- if .Values.backend.database.createSecret -}}
{{- printf "%s-database" (include "cloudops-sre-platform.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- .Values.backend.database.existingSecret -}}
{{- end -}}
{{- end -}}
