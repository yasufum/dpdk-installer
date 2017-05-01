require "yaml"
require "fileutils"

# Overwrite conf in a vars_file stored in group_vars.
def update_var(vars_file, key, val)
  str = ""
  open(vars_file, "r") {|f|
    f.each_line {|l|
      if l.include? "#{key}:"
        str += "#{key}: #{val}\n"
      else
        str += l
      end
    }
  }
  open(vars_file, "w+"){|f| f.write(str)}
end


# Default task
desc "Run tasks for install"
task :default => [
  :confirm_passwd,
  :confirm_sshkey,
  :confirm_http_proxy,
  :install
] do
  puts "done" 
end


desc "Check if sshkey exists and copy from your $HOME/.ssh/id_rsa.pub"
task :confirm_sshkey do
  target = "./roles/common/templates/id_rsa.pub"
  sshkey = "#{ENV['HOME']}/.ssh/id_rsa.pub"
  if not File.exists? target 
    puts "SSH key ocnfiguration."
    puts "> '#{target}' doesn't exist."
    puts "> Please put your public key as '#{target}' for login spp VMs."

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
  if (http_proxy != "") or (http_proxy != yaml['http_proxy'])
    puts "Check proxy configuration."
    puts  "> 'http_proxy' is set to be '#{yaml['http_proxy']}'"
    print "> or use default? (#{http_proxy}) [Y/n]: "
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
            str += "http_proxy: #{new_proxy}\n"
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


desc "Update ansible_ssh_pass and ansible_sudo_pass."
task :confirm_passwd do
  vars_file = "group_vars/all"
  yaml = YAML.load_file(vars_file)
  ["ansible_ssh_pass", "ansible_sudo_pass"].each do |passwd|
    cur_passwd = yaml[passwd]
    # Check if cur_passwd is described in the vars_file
    puts "passwd: #{passwd}"
    puts "cur_passwd: #{cur_passwd}"
    puts yaml
    if cur_passwd == nil
      puts "> input new #{passwd}."
      input_passwd = STDIN.gets.chop

      # Overwrite vars_file with new passwd
      str = ""
      open(vars_file, "r") {|f|
        f.each_line {|l|
          if l.include? passwd
            str += "#{passwd}: #{input_passwd}\n"
          else
            str += l
          end
        }
      }
      open(vars_file, "w+"){|f| f.write(str)}
      puts "> update '#{passwd}' to '#{input_passwd}' in 'group_vars/all'."
    end
  end
end


desc "Dummy task used for debugging"
task :dummy do
  puts "I'm dummy task!"
end


desc "Run ansible playbook"
task :install do
  sh "ansible-playbook -i hosts site.yml"
end


desc "Clean variables depend on user env"
task :clean do
  target = "./roles/common/templates/id_rsa.pub"
  FileUtils.rm_f(target)
  puts "> remove #{target}."

  ["ansible_ssh_pass", "ansible_sudo_pass", "http_proxy"].each do |key|
    update_var("group_vars/all", key, "")
    puts "> clear '#{key}' in 'group_vars/all'."
  end
end
