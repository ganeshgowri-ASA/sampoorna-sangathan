# AGENTS.md - SampoornaSangathan Odoo Custom Addons Guide

## Project: SampoornaSangathan (Unified Organisation OS)
## Platform: Odoo 17 Community Edition
## Working Directory: ~/odoo/custom-addons/
## Database: sampoorna-sangathan
## Odoo URL: http://localhost:8069

---

## Sacred Principles
1. This is an ODOO project - all modules are Python Odoo addons, NOT Next.js/React
2. ONE session = ONE Odoo module in ~/odoo/custom-addons/{module_name}/
3. NEVER modify Odoo core files - only custom-addons/
4. TEST via Odoo shell and module upgrade before committing
5. Each module MUST have proper __manifest__.py with dependencies
6. ROLLBACK if module install fails - never leave DB in broken state

---

## Environment Setup
```
Odoo Path: /home/eechie/odoo/community
Venv: /home/eechie/odoo/venv/bin/python
Config: /home/eechie/odoo/cfg/odoo.conf
Custom Addons: ~/odoo/custom-addons/
DB User: eechie
DB Name: sampoorna-sangathan
```

## Useful Commands
```bash
# Restart Odoo with module update
cd /home/eechie/odoo/community && /home/eechie/odoo/venv/bin/python odoo-bin -d sampoorna-sangathan -c /home/eechie/odoo/cfg/odoo.conf -u {module_name} --stop-after-init

# Install new module
cd /home/eechie/odoo/community && /home/eechie/odoo/venv/bin/python odoo-bin -d sampoorna-sangathan -c /home/eechie/odoo/cfg/odoo.conf -i {module_name} --stop-after-init

# Odoo Shell
cd /home/eechie/odoo/community && /home/eechie/odoo/venv/bin/python odoo-bin shell -d sampoorna-sangathan -c /home/eechie/odoo/cfg/odoo.conf --no-http

# Check module state
psql -U eechie -d "sampoorna-sangathan" -c "SELECT name, state FROM ir_module_module WHERE name LIKE 'sampoorna%' OR name LIKE 'jana%' OR name LIKE 'sambandha%' OR name LIKE 'kosha%' OR name LIKE 'bhandar%' OR name LIKE 'pariyojana%' OR name LIKE 'sutradhara%'"
```

---

## Module Map (22 Total - Phase-wise)

### Phase 1 (Core + 3 modules)
| Module | Directory | Depends On | Description |
|--------|-----------|------------|-------------|
| sampoorna_sangathan_core | sampoorna_sangathan_core/ | base | Branding, dashboard, shared utilities |
| jana_seva_hrms | jana_seva_hrms/ | hr, hr_holidays, hr_attendance, hr_expense | Extended HRMS |
| sambandha_path_crm | sambandha_path_crm/ | crm, sale, sale_management | Extended CRM |
| pariyojana_chakra | pariyojana_chakra/ | project, hr_timesheet | Project Management |

### Phase 2 (Finance + Inventory)
| Module | Directory | Depends On | Description |
|--------|-----------|------------|-------------|
| kosha_prabandhan | kosha_prabandhan/ | account, account_payment | Finance & Accounting |
| bhandar_griha | bhandar_griha/ | stock, purchase | Inventory & Warehouse |
| lekha_peethika | lekha_peethika/ | mail, calendar, contacts | Office Suite |

### Phase 3 (Advanced)
| Module | Directory | Depends On | Description |
|--------|-----------|------------|-------------|
| sutradhara_api | sutradhara_api/ | base | REST API endpoints |
| vidya_kendra | vidya_kendra/ | website, website_slides | eLearning/Knowledge Base |
| niti_rakshak | niti_rakshak/ | base | Compliance & Audit |

---

## Odoo Module Structure Template
```
{module_name}/
  __init__.py
  __manifest__.py
  models/
    __init__.py
    {model_name}.py
  views/
    {model_name}_views.xml
    menu_views.xml
  security/
    ir.model.access.csv
    security_groups.xml
  data/
    {module}_data.xml
  static/
    description/
      icon.png
    src/
      js/
      css/
      xml/
  wizard/
    __init__.py
  reports/
```

## __manifest__.py Template
```python
{
    'name': 'Module Display Name',
    'version': '17.0.1.0.0',
    'category': 'SampoornaSangathan',
    'summary': 'Brief description',
    'description': 'Detailed description',
    'author': 'SampoornaSangathan',
    'website': 'https://sampoorna-sangathan.vercel.app',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
```

---

## Parallel Session Rules
- Each Claude Code session works on EXACTLY ONE module directory
- Sessions must NOT touch files outside their assigned module
- Core module (sampoorna_sangathan_core) must be installed FIRST
- Check dependency modules are installed before testing
- Use `--stop-after-init` flag to avoid port conflicts with running Odoo
- Git: commit to feature branch `feat/{module_name}`, merge to main after QA

## QA Checklist Per Module
1. `__manifest__.py` has correct depends list
2. `ir.model.access.csv` grants proper permissions
3. Module installs without error: `-i {module} --stop-after-init`
4. Module upgrades without error: `-u {module} --stop-after-init`
5. Views load in browser at localhost:8069
6. Menu items appear under SampoornaSangathan category
7. No Python import errors in Odoo logs
8. Security groups properly restrict access
