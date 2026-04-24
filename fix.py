import string

def fix_env():
    with open('.env', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    with open('.env', 'w', encoding='utf-8') as f:
        for line in lines:
            if line.startswith('DATABASE_URL='):
                val = line.split('=', 1)[1]
                # remove any invisible whitespace characters like \r, \n, tabs, spaces, except standard formatting
                cleaned_val = ''.join(c for c in val if ord(c) > 32 and ord(c) < 127)
                f.write(f'DATABASE_URL="{cleaned_val}"\n')
            else:
                f.write(line)

if __name__ == '__main__':
    fix_env()
