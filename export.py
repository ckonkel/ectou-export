    # Create boto session.
#     session = boto3.session.Session()
#     ec2 = session.resource("ec2", args.region)
# 
#     # Resolve source and builder images.
#     source_image = get_image(ec2, args.ami_owner, args.ami_name)
#     builder_image = get_image(ec2, args.builder_ami_owner, args.builder_ami_name)
# 
#     # Resolve VPC if provided, otherwise assume account has default VPC.
#     vpc = None
#     if args.vpc_id:
#         vpc = get_first(ec2.vpcs.filter(VpcIds=[args.vpc_id]))
#     elif args.vpc_name:
#         vpc = get_first(ec2.vpcs.filter(Filters=[{"Name": "tag:Name", "Values": [args.vpc_name]}]))
# 
#     subnet = None
#     if vpc:
#         if args.subnet_id:
#             subnet = get_first(vpc.subnets.filter(SubnetIds=[args.subnet_id]))
#         else:
#             subnet = get_first(vpc.subnets.all())
# 
#     # Set options for explicit VPC, default VPC.
#     vpc_id = vpc.id if vpc else ""
#     subnet_id = subnet.id if subnet else ""
# 
#     # crk@balfour Have option to use private instance
#     if args.private_network == "true":
#         network_type = "private_ip_address"
#         associate_ip = False
#     else:
#         network_type = "public_ip_address"
#         associate_ip = True
# 
#     with resource_cleanup(args.debug) as cleanup:
# 
#         # Create temporary key pair
#         key_pair = ec2.create_key_pair(KeyName=run_name)
#         defer_delete(cleanup, key_pair)
# 
#         # Create temporary security group
#         sg = ec2.create_security_group(GroupName=run_name,
#                                        Description="Temporary security group for ectou-export",
#                                        VpcId=vpc_id)
#         defer_delete(cleanup, sg)
# 
#         # Enable ssh access
#         sg.authorize_ingress(IpPermissions=[dict(
#                 IpProtocol="tcp",
#                 FromPort=22,
#                 ToPort=22,
#                 IpRanges=[dict(CidrIp="0.0.0.0/0")],
#         )])
# 
#         # Launch builder EC2 instance
#         instance = get_first(ec2.create_instances(ImageId=builder_image.id,
#                                                   MinCount=1,
#                                                   MaxCount=1,
#                                                   KeyName=key_pair.name,
#                                                   InstanceType=args.instance_type,
#                                                   NetworkInterfaces=[dict(
#                                                           DeviceIndex=0,
#                                                           SubnetId=subnet_id,
#                                                           Groups=[sg.id],
#                                                           AssociatePublicIpAddress=associate_ip,
#                                                   )]))
#         defer_terminate(cleanup, instance)
# 
#         instance.create_tags(Tags=[{"Key": "Name", "Value": run_name}])
#         instance.wait_until_running()
# 
#         # Attach source image as device
#         attach_ebs_image(ec2, instance, source_image, args.device_name)
# 
#         # Save key pair for ssh
#         with open(PRIVATE_KEY_FILE, "w") as f:
#             os.chmod(PRIVATE_KEY_FILE, 0o600)
#             f.write(key_pair.key_material)
# 
#         print "Network Type: " + network_type
#         print "To access instance for debugging:"
#         print "  ssh -i {} {}@{}".format(PRIVATE_KEY_FILE, args.builder_username, getattr(instance, network_type))
# 
#         ssh_client = connect_ssh(args.builder_username, getattr(instance, network_type), PRIVATE_KEY_FILE)
# 
#         # Export device to vmdk
#         provision_file_put(ssh_client, EXPORT_SCRIPT, "export.sh")
#         provision_shell(ssh_client, ["sudo", "bash", "export.sh", args.device_name, "export.vmdk", args.yum_proxy],
#                         get_pty=True)
#         provision_file_get(ssh_client, "export.vmdk", vmdk)
# 
#     # Package vmdk into vagrant box
#     local_cmd(["bash", PACKAGE_SCRIPT, vmdk, box])
# 
#     # Install guest additions, apply security updates.
#     local_cmd(["bash", GUEST_SCRIPT, box, guestbox])
