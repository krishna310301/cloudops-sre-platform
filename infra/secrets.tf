resource "aws_secretsmanager_secret" "database_url" {
  name                    = "${local.cluster_name}/database"
  description             = "PostgreSQL connection settings for CloudOps SRE Platform"
  recovery_window_in_days = 0

  tags = {
    Name = "${local.cluster_name}-database-secret"
  }
}

resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id = aws_secretsmanager_secret.database_url.id

  secret_string = jsonencode({
    username     = var.db_username
    password     = random_password.db.result
    host         = aws_db_instance.postgres.address
    port         = aws_db_instance.postgres.port
    dbname       = var.db_name
    database_url = "postgresql+psycopg://${var.db_username}:${random_password.db.result}@${aws_db_instance.postgres.address}:${aws_db_instance.postgres.port}/${var.db_name}"
  })
}
