terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# always resolve the current Ubuntu 22.04 LTS AMI for the region, rather than
# hardcoding an AMI id (those go stale and are region-specific)
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_key_pair" "deployctl" {
  key_name   = "${var.project_name}-key"
  public_key = file(var.public_key_path)
}

resource "aws_security_group" "deployctl" {
  name        = "${var.project_name}-sg"
  description = "Ports deployctl needs: SSH for deployment, HTTP/HTTPS for the app behind nginx"

  ingress {
    description = "SSH — locked to allowed_ssh_cidr, not the world"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
  }

  ingress {
    description = "HTTP — for the ACME challenge and the app itself"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # note: the app's container port (core.port in deployctl.conf) is
  # intentionally NOT opened here — only nginx (80/443) is public, so
  # traffic must go through the reverse proxy, not straight to the container

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-sg"
  }
}

resource "aws_instance" "deployctl" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.deployctl.key_name
  vpc_security_group_ids = [aws_security_group.deployctl.id]

  tags = {
    Name = var.project_name
  }
}
