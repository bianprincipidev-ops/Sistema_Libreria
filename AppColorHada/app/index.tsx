import React, { useState, useEffect } from 'react';
import { 
  StyleSheet, Text, View, FlatList, ActivityIndicator, 
  StatusBar, SafeAreaView, TouchableOpacity, Alert, Modal, TextInput 
} from 'react-native';

const API_BASE = 'https://sistema-libreria-er9e.onrender.com';

interface Producto {
  id: number;
  nombre: string;
  precio: number;
  stock: number;
  categoria?: string;
}

export default function App() {
  const [productos, setProductos] = useState<Producto[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  
  // Estados para el nuevo producto
  const [nombre, setNombre] = useState('');
  const [precio, setPrecio] = useState('');
  const [stock, setStock] = useState('');
  const [categoria, setCategoria] = useState('');

  const obtenerProductos = async () => {
    try {
      const respuesta = await fetch(`${API_BASE}/api/productos`);
      const datos = await respuesta.json();
      setProductos(datos);
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setLoading(false);
    }
  };

  const venderProducto = async (id: number) => {
    const formData = new URLSearchParams();
    formData.append('id', id.toString());
    formData.append('cantidad', '1');

    await fetch(`${API_BASE}/vender`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData.toString(),
    });
    obtenerProductos();
  };

  // NUEVA FUNCIÓN: Agregar producto (Igual que el formulario web)
  const agregarProducto = async () => {
    if (!nombre || !precio || !stock) {
      Alert.alert("Error", "Completá los campos básicos");
      return;
    }

    const formData = new URLSearchParams();
    formData.append('nombre', nombre);
    formData.append('precio', precio);
    formData.append('stock', stock);
    formData.append('categoria', categoria);
    formData.append('stock_minimo', '2');

    try {
      await fetch(`${API_BASE}/agregar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData.toString(),
      });
      setModalVisible(false);
      setNombre(''); setPrecio(''); setStock(''); setCategoria('');
      obtenerProductos();
      Alert.alert("Éxito", "Producto agregado correctamente");
    } catch (e) {
      Alert.alert("Error", "No se pudo guardar");
    }
  };

  useEffect(() => { obtenerProductos(); }, []);

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" />
      
      <View style={styles.header}>
        <Text style={styles.titulo}>ColorHada Gestión 🧚‍♀️</Text>
      </View>

      <FlatList
        data={productos}
        keyExtractor={(item) => item.id.toString()}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <View style={{flex: 1}}>
              <Text style={styles.nombre}>{item.nombre}</Text>
              <Text style={styles.precio}>${item.precio} | <Text style={{color: '#666'}}>{item.stock} uni.</Text></Text>
            </View>
            <TouchableOpacity style={styles.btnVender} onPress={() => venderProducto(item.id)}>
              <Text style={styles.btnText}>➔</Text>
            </TouchableOpacity>
          </View>
        )}
        contentContainerStyle={{ padding: 15 }}
      />

      {/* BOTON FLOTANTE PARA AGREGAR (Igual que en las apps modernas) */}
      <TouchableOpacity style={styles.fab} onPress={() => setModalVisible(true)}>
        <Text style={styles.fabText}>+</Text>
      </TouchableOpacity>

      {/* VENTANA EMERGENTE PARA CARGAR PRODUCTO */}
      <Modal visible={modalVisible} animationType="slide" transparent={true}>
        <View style={styles.modalBG}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Nuevo Producto</Text>
            <TextInput placeholder="Nombre" style={styles.input} value={nombre} onChangeText={setNombre} />
            <TextInput placeholder="Precio" style={styles.input} keyboardType="numeric" value={precio} onChangeText={setPrecio} />
            <TextInput placeholder="Stock Inicial" style={styles.input} keyboardType="numeric" value={stock} onChangeText={setStock} />
            <TextInput placeholder="Categoría" style={styles.input} value={categoria} onChangeText={setCategoria} />
            
            <View style={{flexDirection: 'row', justifyContent: 'space-between', marginTop: 10}}>
              <TouchableOpacity style={[styles.btnAction, {backgroundColor: '#ccc'}]} onPress={() => setModalVisible(false)}>
                <Text>Cancelar</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.btnAction, {backgroundColor: '#be185d'}]} onPress={agregarProducto}>
                <Text style={{color: '#fff'}}>Guardar</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fdf2f8' },
  header: { padding: 20, alignItems: 'center', borderBottomWidth: 1, borderBottomColor: '#fce7f3' },
  titulo: { fontSize: 22, fontWeight: 'bold', color: '#be185d' },
  card: { backgroundColor: '#fff', padding: 15, borderRadius: 15, marginBottom: 10, flexDirection: 'row', alignItems: 'center', elevation: 2 },
  nombre: { fontSize: 18, fontWeight: 'bold' },
  precio: { fontSize: 15, color: '#be185d', marginTop: 2 },
  btnVender: { backgroundColor: '#be185d', width: 45, height: 45, borderRadius: 25, justifyContent: 'center', alignItems: 'center' },
  btnText: { color: '#fff', fontSize: 20 },
  fab: { position: 'absolute', bottom: 30, right: 30, backgroundColor: '#be185d', width: 60, height: 60, borderRadius: 30, justifyContent: 'center', alignItems: 'center', elevation: 5 },
  fabText: { color: '#fff', fontSize: 30 },
  modalBG: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', padding: 20 },
  modalContent: { backgroundColor: '#fff', padding: 20, borderRadius: 20 },
  modalTitle: { fontSize: 20, fontWeight: 'bold', marginBottom: 15, textAlign: 'center' },
  input: { borderBottomWidth: 1, borderBottomColor: '#ccc', marginBottom: 15, padding: 8 },
  btnAction: { padding: 15, borderRadius: 10, width: '45%', alignItems: 'center' }
});