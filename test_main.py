import unittest
from unittest.mock import patch, MagicMock
from main import app, buscar_precio

class TestBuscarPrecio(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    @patch('main.login_manager')
    @patch('main.render_template')
    def test_buscar_precio_get_request(self, mock_render, mock_login):
        """Test GET request returns empty results"""
        with self.app.test_request_context('/buscar_precio', method='GET'):
            mock_render.return_value = 'template'
            result = buscar_precio()
            mock_render.assert_called_once()
            call_args = mock_render.call_args
            self.assertEqual(call_args[1]['resultados'], [])
            self.assertEqual(call_args[1]['busqueda'], '')

    @patch('main.conectar')
    @patch('main.render_template')
    def test_buscar_precio_post_request(self, mock_render, mock_conectar):
        """Test POST request with search term"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'nombre': 'Libro Test', 'categoria': 'Ficción'}
        ]
        mock_conn.execute.return_value = mock_cursor
        mock_conectar.return_value = mock_conn
        mock_render.return_value = 'template'

        with self.app.test_request_context('/buscar_precio', method='POST', data={'busqueda': 'Libro'}):
            result = buscar_precio()
            mock_conectar.assert_called_once()
            mock_render.assert_called_once()
            call_args = mock_render.call_args
            self.assertEqual(len(call_args[1]['resultados']), 1)
            self.assertEqual(call_args[1]['busqueda'], 'Libro')
            mock_conn.close.assert_called_once()

    @patch('main.conectar')
    @patch('main.render_template')
    def test_buscar_precio_empty_search(self, mock_render, mock_conectar):
        """Test POST request with empty search term"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.execute.return_value = mock_cursor
        mock_conectar.return_value = mock_conn
        mock_render.return_value = 'template'

        with self.app.test_request_context('/buscar_precio', method='POST', data={'busqueda': ''}):
            result = buscar_precio()
            call_args = mock_render.call_args
            self.assertEqual(call_args[1]['resultados'], [])

if __name__ == '__main__':
    unittest.main()