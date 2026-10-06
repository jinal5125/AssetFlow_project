from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from assets.models import Category, Asset, Employee, Assignment, Maintenance
from datetime import date


class AssetFlowFullTestSuite(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='Password@123'
        )
        self.category = Category.objects.create(
            name='Laptops',
            description='Portable workstations'
        )
        self.employee = Employee.objects.create(
            name='John Doe',
            email='john@example.com',
            department='Engineering',
            phone='+1234567890',
            joining_date='2024-01-15'
        )
        self.asset = Asset.objects.create(
            asset_name='MacBook Pro 16',
            asset_code='LAP-001',
            category=self.category,
            brand='Apple',
            purchase_date='2024-02-01',
            purchase_price=2499.00,
            status='Available'
        )

    # 1. AUTH & LIFECYCLE TESTS
    def test_unauthenticated_root_shows_login_page(self):
        """User opens / -> Must render login page directly"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'assets/login.html')

    def test_unauthenticated_protected_pages_blocked(self):
        """Unauthenticated access to any protected page must redirect to login"""
        protected_urls = [
            '/dashboard/',
            '/assets/',
            '/employees/',
            '/assignments/',
            '/maintenance/',
            '/categories/',
            '/reports/',
            '/export/assets/',
        ]
        for url in protected_urls:
            res = self.client.get(url, follow=False)
            self.assertEqual(res.status_code, 302, f"URL {url} was not protected")
            self.assertIn(reverse('login'), res.url)

    def test_login_page_renders(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'assets/login.html')

    def test_register_flow(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'SecurePassword123!',
            'password2': 'SecurePassword123!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_login_and_logout_full_flow(self):
        """Login -> Dashboard -> Logout -> Login page -> Root blocked"""
        # 1. Login with normal user
        login_res = self.client.post(reverse('login'), {
            'username': 'admin_test',
            'password': 'Password@123'
        }, follow=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertTemplateUsed(login_res, 'assets/dashboard.html')

        # 2. Logout
        logout_res = self.client.get(reverse('logout'), follow=False)
        self.assertEqual(logout_res.status_code, 302)
        self.assertIn(reverse('login'), logout_res.url)

        # 3. Directly opening / after logout must render login page
        post_logout_res = self.client.get('/', follow=False)
        self.assertEqual(post_logout_res.status_code, 200)
        self.assertTemplateUsed(post_logout_res, 'assets/login.html')

    def test_superuser_blocked_from_normal_login(self):
        """Superusers must use /admin/ and are blocked on normal login"""
        User.objects.create_superuser('superadmin', 'super@test.com', 'SuperPass123!')
        res = self.client.post(reverse('login'), {
            'username': 'superadmin',
            'password': 'SuperPass123!'
        })
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Admin accounts must use the Django Admin panel')

    def test_dashboard_authenticated(self):
        self.client.login(username='admin_test', password='Password@123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'assets/dashboard.html')

    # 3. ASSET CRUD & LIFECYCLE
    def test_assets_list_authenticated(self):
        self.client.login(username='admin_test', password='Password@123')
        response = self.client.get(reverse('assets_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'MacBook Pro 16')

    def test_add_asset(self):
        self.client.login(username='admin_test', password='Password@123')
        response = self.client.post(reverse('add_asset'), {
            'asset_name': 'Dell XPS 15',
            'asset_code': 'LAP-002',
            'category': self.category.id,
            'brand': 'Dell',
            'purchase_date': '2024-03-01',
            'purchase_price': '1800.00'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Asset.objects.filter(asset_code='LAP-002').exists())


    def test_public_asset_detail(self):
        response = self.client.get(reverse('asset_detail', args=[self.asset.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'MacBook Pro 16')

    # 4. CATEGORY CRUD
    def test_categories_list(self):
        self.client.login(username='admin_test', password='Password@123')
        response = self.client.get(reverse('categories_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Laptops')

    def test_add_category(self):
        self.client.login(username='admin_test', password='Password@123')
        response = self.client.post(reverse('add_category'), {
            'name': 'Monitors',
            'description': 'Display devices'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Category.objects.filter(name='Monitors').exists())

    # 5. ASSIGNMENTS & RETURN FLOW
    def test_assignment_and_return_lifecycle(self):
        self.client.login(username='admin_test', password='Password@123')
        # Assign
        response = self.client.post(reverse('add_assignment'), {
            'asset': self.asset.id,
            'employee': self.employee.id,
            'assigned_date': '2024-04-01',
            'remarks': 'Assigned for project work'
        })
        self.assertEqual(response.status_code, 302)
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, 'Assigned')

        assignment = Assignment.objects.get(asset=self.asset, returned_date__isnull=True)
        # Return
        response = self.client.post(reverse('return_asset', args=[assignment.id]), {
            'returned_date': '2024-05-01'
        })
        self.assertEqual(response.status_code, 302)
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, 'Available')

    # 6. MAINTENANCE FLOW
    def test_maintenance_lifecycle(self):
        self.client.login(username='admin_test', password='Password@123')
        # Add Maintenance
        response = self.client.post(reverse('add_maintenance'), {
            'asset': self.asset.id,
            'issue': 'Battery overheating',
            'reported_date': '2024-06-01',
            'remarks': 'Sent to service center'
        })
        self.assertEqual(response.status_code, 302)
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, 'Maintenance')

        maint = Maintenance.objects.get(asset=self.asset, status='Open')
        # Complete Maintenance -> asset should become Available
        response = self.client.post(reverse('edit_maintenance', args=[maint.id]), {
            'issue': 'Battery replaced',
            'status': 'Completed',
            'repair_date': '2024-06-10',
            'repair_cost': '150.00',
            'remarks': 'Fixed under warranty'
        })
        self.assertEqual(response.status_code, 302)
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, 'Available')

    # 7. REPORTS & CSV EXPORTS
    def test_reports_view(self):
        self.client.login(username='admin_test', password='Password@123')
        response = self.client.get(reverse('reports'))
        self.assertEqual(response.status_code, 200)

    def test_csv_exports(self):
        self.client.login(username='admin_test', password='Password@123')
        res1 = self.client.get(reverse('export_assets_csv'))
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1['Content-Type'], 'text/csv')

        res2 = self.client.get(reverse('export_assignments_csv'))
        self.assertEqual(res2.status_code, 200)

        res3 = self.client.get(reverse('export_maintenance_csv'))
        self.assertEqual(res3.status_code, 200)
