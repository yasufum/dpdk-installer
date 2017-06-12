require "yaml"
require "fileutils"

# Set up variables for use specific info
#
# [memo]
# This script asks user specific params and is sensitive for the difference
# between "" and nil loaded from YAML to recognize it is already
# set or not("" means already set).
# It doesn't ask for params which are set "" to avoid redundant question.
# If you run 'rake clean', target params are set to nil.

# Overwrite conf in a vars_file stored in group_vars.
# Last arg 'clean_flg' is true if running 'rake clean' to make val empty,
# or false to set val as "" which means it's set to no value
# but not empty for recognizing it's already set.
#   key:     # true
#   key: ""  # false
def update_var(vars_file, key, val, clean_flg=false)
  str = ""
  open(vars_file, "r") {|f|
    f.each_line {|l|
      if l.include? "#{key}:"
        if clean_flg == false
          str += "#{key}: \"#{val}\"\n"
        else
          str += "#{key}: #{val}\n"
        end
      else
        str += l
      end
    }
  }

  # Check if key is included in vars_file
  if !str.include? key
    raise "Error: There is no attribute '#{key}'!"
  end

  open(vars_file, "w+"){|f| f.write(str)}
end


# Clean hosts
# Remove other than string starting "[", "#" or "\n"
def clean_hosts()
  str = ""
  hosts_file = "hosts"
  open(hosts_file, "r") {|f|
    f.each_line {|l|
      if l =~ /^(\[|#|\n)/ # match "[", "#" or "\n"
        str += l
      end
    }
  }
  open(hosts_file, "w+") {|f| f.write(str)}
end


# Return pretty formatted memsize
#   params
#     - memsize: Memory size as string or integer
#     - unit: Unit of memsize (k, m or g) 
def pretty_memsize(memsize, unit=nil)
  if unit == nil
    un = 1
  elsif unit == "k"
    un = 1_000
  elsif unit == "m"
    un = 1_000_000
  elsif unit == "g"
    un = 1_000_000_000
  end
  res = memsize.to_i * un

  len = res.to_s.size 
  if len < 4 
    return res.to_s + " B"
  elsif len < 7
    return (res/1_000).to_i.to_s + " kB"
  elsif len < 10
    return (res/1_000_000).to_i.to_s + " MB"
  elsif len < 13
    return (res/1_000_000_000).to_i.to_s + " GB"
  elsif len < 16
    return (res/1_000_000_000_000).to_i.to_s + " TB"
  elsif len < 19
    return (res/1_000_000_000_000_000).to_i.to_s + " PB"
  elsif len < 22
    return (res/1_000_000_000_000_000_000).to_i.to_s + " EB"
  else
    return (res/1_000_000_000_000_000_000_000).to_i.to_s  + " ZB"
  end
end


# Default task
desc "Run tasks for install"
task :default => [
  :confirm_account,
  :confirm_sshkey,
  :confirm_http_proxy,
  :confirm_dpdk,
  :install
] do
  puts "done" 
end


desc "Check if sshkey exists and copy from your $HOME/.ssh/id_rsa.pub"
task :confirm_sshkey do
  target = "./roles/common/templates/id_rsa.pub"
  sshkey = "#{ENV['HOME']}/.ssh/id_rsa.pub"
  if not File.exists? target 
    puts "SSH key configuration."
    puts "> '#{target}' doesn't exist."
    puts "> Please put your public key as '#{target}' for target machines."

    if File.exists? sshkey
      print "> copy '#{sshkey}' to '#{target}'? [y/N]"
      ans = STDIN.gets.chop
      if ans.downcase == "y" or ans.downcase == "yes"
        FileUtils.mkdir_p("#{ENV['HOME']}/.ssh")
        FileUtils.copy(sshkey, target)
      end
    else
      puts "> If you don't have the key, generate and put it as following."
      puts "> $ ssh-keygen"
      puts "> # Use default for all of input you're asked"
      puts "> $ cp $HOME/.ssh/id_rsa.pub #{target}"
      exit  # Terminate install
    end
  end
end


# Ask using default value or new one.
desc "Check http_proxy setting"
task :confirm_http_proxy do
  http_proxy = ENV["http_proxy"]
  vars_file = "group_vars/all"
  yaml = YAML.load_file(vars_file)
  # Check if http_proxy same as your env is described in the vars_file
  if yaml['http_proxy'] == nil
    if (http_proxy != "") or (http_proxy != yaml['http_proxy'])
      puts "Check proxy (Type enter with no input if you are not in proxy env)."
      puts  "> 'http_proxy' is set as '#{yaml['http_proxy']}'."
      print "> Use proxy env ? (#{http_proxy}) [Y/n]: "
      ans = STDIN.gets.chop
      if ans.downcase == "n" or ans.downcase == "no"
        print "> http_proxy: "
        new_proxy = STDIN.gets.chop
      else
        new_proxy = http_proxy
      end
  
      if yaml['http_proxy'] != new_proxy
        # update proxy conf
        str = ""  # contains updated contents of vars_file to write new one
        open(vars_file, "r") {|f|
          f.each_line {|l|
            if l.include? "http_proxy:"
              str += "http_proxy: \"#{new_proxy}\"\n"
            else
              str += l
            end
          }
        }
        open(vars_file, "w+"){|f| f.write(str)}
        puts "> update 'http_proxy' to '#{new_proxy}' in 'group_vars/all'."
      else
        puts "> proxy isn't changed."
      end
    end
  end
end


desc "Update remote_user, ansible_ssh_pass and ansible_sudo_pass."
task :confirm_account do
  target_params = ["remote_user", "ansible_ssh_pass", "ansible_sudo_pass"]
  vars_file = "group_vars/all"
  yaml = YAML.load_file(vars_file)
  target_params.each do |account_info|
    cur_info = yaml[account_info]
    # Check if cur_info is described in the vars_file
    if cur_info == nil
      puts "> input new #{account_info}."
      input_info = STDIN.gets.chop

      # Overwrite vars_file with new one 
      str = ""
      open(vars_file, "r") {|f|
        f.each_line {|l|
          if l.include? account_info
            str += "#{account_info}: #{input_info}\n"
          else
            str += l
          end
        }
      }
      open(vars_file, "w+"){|f| f.write(str)}
      puts "> update '#{account_info}' to '#{input_info}' in 'group_vars/all'."
    end
  end
end


desc "Setup DPDK params (hugepages and network interfaces)"
task :confirm_dpdk do
  vars_file = "group_vars/dpdk"

  puts "Input params for DPDK"
  puts "> hugepage_size (must be 2m(2M) or 1g(1G)):"
  ans = ""
  while not (ans == "2M" or ans == "1G")
    ans = STDIN.gets.chop.upcase
    if not (ans == "2M" or ans == "1G")
      puts "> Error! Invalid parameter."
      puts "> hugepage_size (must be 2M or 1G):"
    end
  end
  hp_size = ans
  update_var(vars_file, "hugepage_size", hp_size, false)
  #puts "hugepage_size: #{hp_size}"

  puts "> nr_hugepages:"
  ans = STDIN.gets.chop
  nr_hp = ans
  if hp_size == "2M"
    total_hpmem = 2_000_000 * nr_hp.to_i
  elsif hp_size == "1G"
    total_hpmem = 1_000_000_000 * nr_hp.to_i
  end
  total_hpmem = pretty_memsize(total_hpmem)
  puts "> total hugepages mem: #{total_hpmem}"
  update_var(vars_file, "nr_hugepages", nr_hp, false)

  puts "> dpdk_interfaces (separate by space if two or more):"
  delim = " "
  ans = STDIN.gets.chop
  nw_ifs = ans.split(delim).join(delim)
  #puts "nw interfaces: #{nw_ifs}"
  update_var(vars_file, "dpdk_interfaces", nw_ifs, false)

  puts "> dpdk_target (must be '(i)vshmem' for SPP or '(n)ative'):"
  ans = ""
  while not (ans == "ivshmem" or ans == "native")
    ans = STDIN.gets.chop
    if ans == "i"
      ans = "ivshmem"
    elsif ans == "n"
      ans = "native"
    end
    if not (ans == "ivshmem" or ans == "native")
      puts "> Error! Invalid parameter."
      puts "> dpdk_target (must be 'ivshmem' for SPP or 'native'):"
    end
  end
  if ans == "ivshmem"
    dpdk_tgt = "x86_64-ivshmem-linuxapp-gcc"
  else
    dpdk_tgt = "x86_64-native-linuxapp-gcc"
  end
  #puts "dpdk_target: #{dpdk_tgt}"
  update_var(vars_file, "dpdk_target", dpdk_tgt, false)
end


task :dummy do
  puts "I'm dummy task!"
end


desc "Run ansible playbook"
task :install do
  vars_file = "group_vars/all"
  yaml = YAML.load_file(vars_file)
  if yaml["http_proxy"] == nil or yaml["http_proxy"] == "" 
    sh "ansible-playbook -i hosts site.yml"
  else
    sh "ansible-playbook -i hosts site_proxy.yml"
  end
end


desc "Clean variables"
task :clean_vars do
  # "group_vars/all"
  target_params = [
    "remote_user", "ansible_ssh_pass", "ansible_sudo_pass", "http_proxy"
  ]
  # remove ssh user account form vars file.
  vars_file = "group_vars/all"
  target_params.each do |key|
    update_var(vars_file, key, "", true)
    puts "> clear '#{key}' in '#{vars_file}'."
  end

  # "group_vars/dpdk"
  target_params = [
    "hugepage_size", "nr_hugepages", "dpdk_interfaces", "dpdk_target"
  ]
  # remove ssh user account form vars file.
  vars_file = "group_vars/dpdk"
  target_params.each do |key|
    update_var(vars_file, key, "", true)
    puts "> clear '#{key}' in '#{vars_file}'."
  end
end


desc "Clean hosts file"
task :clean_hosts do
  # clean hosts file
  clean_hosts()
  puts "> clean hosts"
end


desc "Remove sshkey file"
task :remove_sshkey do
  # remove public key from templates
  target = "./roles/common/templates/id_rsa.pub"
  FileUtils.rm_f(target)
  puts "> remove #{target}."
end


desc "Clean variables and files depend on user env"
task :clean => [
  :clean_vars,
  :clean_hosts,
  :remove_sshkey
] do
  sh "rm -f *.retry"
end
