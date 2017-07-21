require "yaml"
require "fileutils"
$:.unshift(File.dirname(__FILE__) + "/lib")
require "rake_utils.rb"

# Default task
desc "Run tasks for install"
task :default => [
  :check_hosts,
  :confirm_account,
  :confirm_sshkey,
  :confirm_http_proxy,
  :confirm_dpdk,
  :install
] do
  puts "Done" 
end


desc "Configure params"
task :config => [
  :check_hosts,
  :confirm_account,
  :confirm_sshkey,
  :confirm_http_proxy,
  :confirm_dpdk,
] do
  puts "Done"
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
  vars_file = "group_vars/all"
  yaml = YAML.load_file(vars_file)
  ["http_proxy", "https_proxy"].each do |proxy|
    # Check if http_proxy same as your env is described in the vars_file
    if yaml[proxy] == nil
      if (ENV[proxy] != "") or (ENV[proxy] != yaml[proxy])
        puts "Check proxy (Type enter with no input if you are not in proxy env)."
        puts  "> '#{proxy}' is set as '#{yaml[proxy]}'."
        print "> Use proxy env ? (#{ENV[proxy]}) [Y/n]: "
        ans = STDIN.gets.chop
        if ans.downcase == "n" or ans.downcase == "no"
          print "> #{proxy}: "
          new_proxy = STDIN.gets.chop
        else
          new_proxy = ENV[proxy]
        end

        if yaml[proxy] != new_proxy
          # update proxy conf
          str = ""  # contains updated contents of vars_file to write new one
          open(vars_file, "r") {|f|
            f.each_line {|l|
              if l.include? "#{proxy}:"
                str += "#{proxy}: \"#{new_proxy}\"\n"
              else
                str += l
              end
            }
          }
          open(vars_file, "w+"){|f| f.write(str)}
          puts "> update #{proxy} to '#{new_proxy}' in 'group_vars/all'."
        else
          puts "> proxy isn't changed."
        end
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
  # There are three vars_files including params related to DPDK.
  #   1. group_vars/dpdk
  #   2. group_vars/pktgen
  #   3. group_vars/spp
  # In this task, setup all of files by asking user some questions and update
  # vars_files. 
  # Skip updating if vars_files are already setup.
  #
  # [NOTE] It asks only for dpdk and not others because all of vars are included
  # in dpdk's var file. It's needed to be asked for other files if they include
  # vars not included dpdk.
  
  # 1. Update group_vars/dpdk 
  vars_file = "group_vars/dpdk"
  yaml = YAML.load_file(vars_file)

  target_params = {
    "hugepage_size" => nil,
    "nr_hugepages" => nil,
    "dpdk_interfaces" => nil,
    "dpdk_target" => nil
  }

  # Check if all params are filled for confirm vars_file is already setup
  target_params.each do |param, val|
    if yaml[param] == nil
      puts "Input params for DPDK"
      break
    end
  end

  target_params.each do |param, val|
    case param
    when "hugepage_size"
      if yaml["hugepage_size"] == nil
        puts "> hugepage_size (must be 2m(2M) or 1g(1G)):"
        ans = ""
        while not (ans == "2M" or ans == "1G")
          ans = STDIN.gets.chop.upcase
          if not (ans == "2M" or ans == "1G")
            puts "> Error! Invalid parameter."
            puts "> hugepage_size (must be 2m(2M) or 1g(1G)):"
          end
        end
        hp_size = ans
        update_var(vars_file, "hugepage_size", hp_size, false)
        target_params[param] = hp_size
        #puts "hugepage_size: #{hp_size}"
      else
        target_params[param] = yaml[param]
      end
  
    # [NOTE] "hugepage_size" must be decided before "nr_hugepages" because it's
    # refered in this section.
    when "nr_hugepages"
      if yaml["nr_hugepages"] == nil
        puts "> nr_hugepages:"
        ans = STDIN.gets.chop
        nr_hp = ans
        hp_size = target_params["hugepage_size"]
        if hp_size == "2M"
          total_hpmem = 2_000_000 * nr_hp.to_i
        elsif hp_size == "1G"
          total_hpmem = 1_000_000_000 * nr_hp.to_i
        else
          raise "Error! Invalid hugepage_size: #{hp_size}"
        end
        total_hpmem = pretty_memsize(total_hpmem)
        puts "> total hugepages mem: #{total_hpmem}"
        update_var(vars_file, "nr_hugepages", nr_hp, false)
        target_params[param] = nr_hp
      else
        target_params[param] = yaml[param]
      end
  
    when "dpdk_interfaces"
      if yaml["dpdk_interfaces"] == nil
        puts "> dpdk_interfaces (separate by space if two or more):"
        delim = " "  # input is separated with white spaces
        ans = STDIN.gets.chop
        nw_ifs = ans.split(delim).join(delim) # formatting by removing nouse chars
        #puts "nw interfaces: #{nw_ifs}"
        update_var(vars_file, "dpdk_interfaces", nw_ifs, false)
        target_params[param] = nw_ifs
      else
        target_params[param] = yaml[param]
      end
  
    when "dpdk_target"
      if yaml["dpdk_target"] == nil
        puts "> dpdk_target (use '(i)vshmem' for SPP or '(n)ative'):"
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
            puts "> dpdk_target (use 'ivshmem' for SPP or 'native'):"
          end
        end
        if ans == "ivshmem"
          dpdk_tgt = "x86_64-ivshmem-linuxapp-gcc"
        else
          dpdk_tgt = "x86_64-native-linuxapp-gcc"
        end
        #puts "dpdk_target: #{dpdk_tgt}"
        update_var(vars_file, "dpdk_target", dpdk_tgt, false)
        target_params[param] = dpdk_tgt
      else
        target_params[param] = yaml[param]
      end
    end
  end

  # 2. Update group_vars/pktgen
  update_var(
    "group_vars/pktgen",
    "dpdk_target",
    target_params["dpdk_target"],
    false
  )

  # 3. Update group_vars/spp
  update_var(
    "group_vars/spp",
    "dpdk_target",
    target_params["dpdk_target"],
    false
  )
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
    "remote_user",
    "ansible_ssh_pass",
    "ansible_sudo_pass",
    "http_proxy",
    "https_proxy"
  ]
  # remove ssh user account form vars file.
  vars_file = "group_vars/all"
  target_params.each do |key|
    update_var(vars_file, key, "", true)
    puts "> clean '#{key}' in '#{vars_file}'."
  end

  # 1. "group_vars/dpdk"
  target_params = [
    "hugepage_size",
    "nr_hugepages",
    "dpdk_interfaces",
    "dpdk_target"
  ]
  # remove ssh user account form vars file.
  vars_file = "group_vars/dpdk"
  target_params.each do |key|
    update_var(vars_file, key, "", true)
    puts "> clean '#{key}' in '#{vars_file}'."
  end

  # 2. "group_vars/pktgen"
  key = "dpdk_target"
  vars_file = "group_vars/pktgen"
  update_var(vars_file, key, "", true)
  puts "> clean '#{key}' in '#{vars_file}'."

  # 3. "group_vars/spp"
  key = "dpdk_target"
  vars_file = "group_vars/spp"
  update_var(vars_file, key, "", true)
  puts "> clean '#{key}' in '#{vars_file}'."
end


desc "Check hosts file is configured"
task :check_hosts do
  if not is_hosts_configured()
    raise "Error! You must setup 'hosts' first."
  end
end


desc "Save config"
task :save_conf do
  dst_dir = "tmp/config"
  # mkdir dst and child dir
  sh "mkdir -p #{dst_dir}/group_vars"

  sh "cp hosts #{dst_dir}/"
  sh "cp group_vars/* #{dst_dir}/group_vars/"
end


desc "Restore config"
task :restore_conf do
  dst_dir = "tmp/config"

  sh "cp #{dst_dir}/hosts hosts"
  sh "cp #{dst_dir}/group_vars/* group_vars/"
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
