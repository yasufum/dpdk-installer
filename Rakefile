require "yaml"
require "fileutils"

# Overwrite proxy conf in vars_file (usually, group_vars/all)
def update_proxy_var(vars_file, new_proxy)
  str = ""
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
end


# Default task
task :default => [
  :confirm_sshkey,
  :confirm_http_proxy,
  :dummy
] do
  puts "done" 
end


# Check if sshkey exists and copy from your $HOME/.ssh/id_rsa.pub
task :confirm_sshkey do
  target = "./roles/common/templates/id_rsa.pub"
  sshkey = "#{ENV['HOME']}/.ssh/id_rsa.pub"
  if not File.exists? target 
    puts "SSH key ocnfiguration."
    puts "> '#{target}' doesn't exist."
    puts "> Please put your public key as '#{target}' for login spp VMs."

    if File.exists? sshkey
      print "> copy '#{sshkey}' to '#{target}'? [y/N]"
      ans = gets.chop
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


# Check http_proxy setting
# Ask using default value or new one.
task :confirm_http_proxy do
  http_proxy = ENV["http_proxy"]
  vars_file = "group_vars/all"
  yaml = YAML.load_file(vars_file)
  if (http_proxy != "") or (http_proxy != yaml['http_proxy'])
    puts "Check proxy configuration."
    puts  "> 'http_proxy' is set to be '#{yaml['http_proxy']}'"
    print "> or use default? (#{http_proxy}) [Y/n]: "
    ans = gets.chop
    if ans.downcase == "n" or ans.downcase == "no"
      print "> http_proxy: "
      new_proxy = gets.chop
    else
      new_proxy = http_proxy
    end

    if yaml['http_proxy'] != new_proxy
      # update proxy conf
      str = ""
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


# Dummy used instead of install task for debugging
task :dummy do
  puts "I'm dummy task!"
end


# Do ansible playbook
task :install do
  sh "ansible-playbook -i hosts site.yml"
end


# Clean variables depend on user env
task :clean do
  target = "./roles/common/templates/id_rsa.pub"
  FileUtils.rm_f(target)
  puts "> remove #{target}."

  update_proxy_var("group_vars/all", "")
  puts "> clear 'http_proxy' in 'group_vars/all'."
end
