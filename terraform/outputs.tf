output "public_ip" {
  description = "Public IP of the provisioned VPS — put this in deployctl's .env as VPS_IP"
  value       = aws_instance.deployctl.public_ip
}

output "public_dns" {
  description = "Public DNS name of the instance"
  value       = aws_instance.deployctl.public_dns
}

output "ssh_command" {
  description = "Quick way to SSH in and verify before running deployctl"
  value       = "ssh -i ~/.ssh/deployctl_aws ubuntu@${aws_instance.deployctl.public_ip}"
}
