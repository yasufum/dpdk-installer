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


# Check host is setup
# Return false if hosts is not configured.
def is_hosts_configured()
  ary = []
  hosts_file = "hosts"
  open(hosts_file, "r") {|f|
    f.each_line {|l|
      if not (l =~ /^(\[|#|\n)/) # match lines doesn't start from "[", "#" or "\n"
        ary << l
      end
    }
  }
  if ary.size == 0
    return false
  else
    return true
  end
end


# Clean hosts
# Remove other than string starting "[", "#" or "\n"
def clean_hosts()
  str = ""
  hosts_file = "hosts"
  open(hosts_file, "r") {|f|
    f.each_line {|l|
      if l =~ /^(\[|#|\n)/ # match lines starting from "[", "#" or "\n"
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
  un = nil
  case unit
  when nil
    un = 1
  when "k"
    un = 1_000
  when "m"
    un = 1_000_000
  when "g"
    un = 1_000_000_000
  else
    raise "Error! Invalid unit '#{unit}'"
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
