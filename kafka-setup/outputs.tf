# ---------------------------------------------
#    Main Module Output return variables
# ---------------------------------------------

output "node01_public_ip" {
  value = join("",["ssh -i ", var.ssh_private_key_path," ubuntu@", module.node01.public_ip])
}

output "node01_public_dns" {
  value = join("",["http://",module.node01.public_dns,":3000"])
}