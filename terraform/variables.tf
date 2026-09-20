variable "aws_region" {
  description = "AWS region to provision the VPS in"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Used to tag/name resources — should match core.project_name in deployctl.conf"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type (t2.micro is AWS free-tier eligible)"
  type        = string
  default     = "t2.micro"
}

variable "public_key_path" {
  description = "Path to the local SSH public key to install on the instance (generate a dedicated one, don't reuse an unrelated key)"
  type        = string
  default     = "~/.ssh/deployctl_aws.pub"
}

variable "allowed_ssh_cidr" {
  description = "CIDR block allowed to SSH in on port 22 — set this to your own IP/32, not 0.0.0.0/0"
  type        = string
}
