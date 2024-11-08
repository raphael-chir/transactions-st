# ----------------------------------------
#        Compute module Main
# ----------------------------------------


# Create ec2 instance
resource "aws_instance" "this" {
  ami                         = var.ami_id
  instance_type               = var.instance_type
  key_name                    = var.ssh_public_key_name
  associate_public_ip_address = true
  vpc_security_group_ids      = var.vpc_security_group_ids
  subnet_id                   = var.subnet_id
  user_data = templatefile(var.user_data_script_path, var.user_data_args)
  tags = {
    Name        = join("-",[var.base_name, var.resource_tags["project"],var.resource_tags["environment"]])
    Project     = var.resource_tags["project"]
    Owner       = var.resource_tags["owner"]
    Environment = var.resource_tags["environment"]
    user        = var.resource_tags["user"]
  }
  root_block_device {
    volume_size           = 16        # Taille du disque en Go
    volume_type           = "gp3"     # Type de volume (gp2, gp3, io1, io2, sc1, st1)
    delete_on_termination = true      # Supprimer le volume à la suppression de l'instance
    encrypted             = true      # Activer le chiffrement
  }
}