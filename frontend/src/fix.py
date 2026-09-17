import re

source = r'C:\Users\nikhi\OneDrive\Desktop\NavCare\frontend\src\App.jsx'
dest = r'C:\Users\nikhi\OneDrive\Desktop\Disha\frontend\src\App.jsx'

with open(source, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Branding
content = content.replace('NavCare', 'Disha')
content = content.replace('District Hospital Sagar', 'Powered by AWS Cloud')
content = content.replace('जिला अस्पताल सागर', 'Powered by AWS Cloud')
content = content.replace('navcare_session_id', 'disha_session_id')

# 2. Colors
content = content.replace('blue-600', 'orange-500')
content = content.replace('blue-700', 'orange-600')
content = content.replace('blue-500', 'orange-400')
content = content.replace('blue-400', 'orange-300')
content = content.replace('blue-300', 'orange-200')
content = content.replace('blue-100', 'orange-100')
content = content.replace('blue-50', 'orange-50')
content = content.replace('blue-900', 'orange-900')
content = content.replace('blue-800', 'orange-800')
content = content.replace('blue-200', 'orange-200')
content = content.replace('rgba(37,99,235,0.39)', 'rgba(249,115,22,0.39)')

# 3. Logo Icon (Map Pin -> Cloud)
pin_svg1 = '<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />'
pin_svg2 = '<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />'
cloud_svg = '<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />'

content = content.replace(pin_svg1 + '\n              ' + pin_svg2, cloud_svg)
content = content.replace(pin_svg1 + '\n            ' + pin_svg2, cloud_svg)

# 4. Remove Header Buttons (Stats & Lang)
header_buttons_regex = r'<button\s+onClick=\{handleOpenStats\}.*?</button>\s*<button\s+onClick=\{[^\}]*setIsDarkMode[^\}]*\}.*?</button>\s*<div className="flex items-center bg-gray-100.*?>.*?</div>'
replacement = '<button onClick={() => setIsDarkMode(!isDarkMode)} className="p-2 text-gray-500 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full transition-colors" title={isDarkMode ? "Light Mode" : "Dark Mode"}>{isDarkMode ? <Sun size={20} /> : <Moon size={20} />}</button>'
content = re.sub(header_buttons_regex, replacement, content, flags=re.DOTALL)

# 5. Remove Watermark
watermark_regex = r'\{\/\* Watermark & Contact \*\/\}.*?</div>'
content = re.sub(watermark_regex, '', content, flags=re.DOTALL)

with open(dest, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed App.jsx successfully!")
