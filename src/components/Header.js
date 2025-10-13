import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { FiUser, FiLogOut, FiMenu, FiX, FiHome, FiUpload, FiImage } from 'react-icons/fi';
import './Header.css';

const Header = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
    setIsMobileMenuOpen(false);
  };

  const isActive = (path) => {
    return location.pathname === path;
  };

  const navItems = [
    { path: '/dashboard', label: '首页', icon: FiHome },
    { path: '/upload', label: '上传', icon: FiUpload },
    { path: '/gallery', label: '相册', icon: FiImage }
  ];

  return (
    <header className="header">
      <div className="container">
        <div className="header-content">
          {/* Logo */}
          <Link to="/dashboard" className="logo">
            <div className="logo-icon">V</div>
            <span className="logo-text">PhotoVault</span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="nav-desktop">
            {user && navItems.map(({ path, label, icon: Icon }) => (
              <Link
                key={path}
                to={path}
                className={`nav-link ${isActive(path) ? 'active' : ''}`}
              >
                <Icon className="nav-icon" />
                {label}
              </Link>
            ))}
          </nav>

          {/* User Menu */}
          {user ? (
            <div className="user-menu">
              <div className="user-info">
                <FiUser className="user-icon" />
                <span className="username">{user.username}</span>
              </div>
              <button onClick={handleLogout} className="logout-btn">
                <FiLogOut />
                退出
              </button>
            </div>
          ) : (
            <div className="auth-buttons">
              <Link to="/login" className="btn btn-secondary">
                登录
              </Link>
              <Link to="/register" className="btn btn-primary">
                注册
              </Link>
            </div>
          )}

          {/* Mobile Menu Button */}
          <button
            className="mobile-menu-btn"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          >
            {isMobileMenuOpen ? <FiX /> : <FiMenu />}
          </button>
        </div>

        {/* Mobile Navigation */}
        {isMobileMenuOpen && (
          <nav className="nav-mobile">
            {user && navItems.map(({ path, label, icon: Icon }) => (
              <Link
                key={path}
                to={path}
                className={`nav-link ${isActive(path) ? 'active' : ''}`}
                onClick={() => setIsMobileMenuOpen(false)}
              >
                <Icon className="nav-icon" />
                {label}
              </Link>
            ))}
            {user && (
              <button onClick={handleLogout} className="logout-btn mobile">
                <FiLogOut />
                退出登录
              </button>
            )}
            {!user && (
              <div className="auth-buttons mobile">
                <Link 
                  to="/login" 
                  className="btn btn-secondary"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  登录
                </Link>
                <Link 
                  to="/register" 
                  className="btn btn-primary"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  注册
                </Link>
              </div>
            )}
          </nav>
        )}
      </div>
    </header>
  );
};

export default Header;
