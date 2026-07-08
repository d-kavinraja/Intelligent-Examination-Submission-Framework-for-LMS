import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  Bell,
  ChevronDown,
  LayoutDashboard,
  CreditCard,
  BarChart3,
  ClipboardList,
  LogOut,
  User,
  Settings,
  LifeBuoy
} from 'lucide-react';

export type PortalTab = 'Dashboard' | 'Submissions' | 'Analytics' | 'Support Desk' | 'Profile' | 'Settings';

interface PortalNavbarProps {
  fullName: string;
  username: string;
  activeTab: PortalTab;
  onTabChange: (tab: PortalTab) => void;
  onLogout?: () => void;
  moodleUserId?: number;
  sessionId?: string;
}

const navItems: { label: PortalTab; icon: React.ElementType }[] = [
  { label: 'Dashboard', icon: LayoutDashboard },
  { label: 'Submissions', icon: ClipboardList },
  { label: 'Analytics', icon: BarChart3 },
  { label: 'Support Desk', icon: LifeBuoy },
  { label: 'Profile', icon: User },
  { label: 'Settings', icon: Settings },
];

export function PortalNavbar({ fullName, username, activeTab, onTabChange, onLogout, moodleUserId, sessionId }: PortalNavbarProps) {
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [imgFailed, setImgFailed] = useState(false);
  const navigate = useNavigate();

  const initials = fullName
    ? fullName
      .split(' ')
      .slice(0, 2)
      .map(n => n[0])
      .join('')
      .toUpperCase()
    : 'U';

  const avatarUrl = sessionId
    ? `http://localhost:8000/student/avatar?session=${sessionId}`
    : moodleUserId
      ? `https://lms2.ai.saveetha.in/user/pix.php/${moodleUserId}/f2.jpg`
      : null;

  const handleLogout = () => {
    localStorage.removeItem('student_credentials');
    if (onLogout) onLogout();
    navigate('/portal/student/login');
  };

  const [drawerOpen, setDrawerOpen] = useState(false);

  return (
    <>
      <nav className="portal-navbar">
        {/* Hamburger (Tablet & Mobile only) */}
        <button 
          className="portal-hamburger" 
          onClick={() => setDrawerOpen(true)}
          aria-label="Open Menu"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="4" x2="20" y1="12" y2="12" />
            <line x1="4" x2="20" y1="6" y2="6" />
            <line x1="4" x2="20" y1="18" y2="18" />
          </svg>
        </button>

        {/* Brand */}
        <div className="portal-brand">
          <div className="portal-brand-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M2 17L12 22L22 17" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M2 12L12 17L22 12" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <span className="portal-brand-name">Student Portal</span>
        </div>

        {/* Nav Items (Desktop only) */}
        <div className="portal-nav-items">
          {navItems.map(item => (
            <button
              key={item.label}
              onClick={() => onTabChange(item.label)}
              className={`portal-nav-item ${activeTab === item.label ? 'active' : ''}`}
            >
              <item.icon size={15} />
              {item.label}
            </button>
          ))}
        </div>

        {/* Right Side */}
        <div className="portal-nav-right">
          {/* Notifications */}
          <div style={{ position: 'relative' }}>
            <motion.button
              className="portal-notif-btn"
              whileHover={{ scale: 1.02 }}
              onClick={() => setShowNotifications(!showNotifications)}
            >
              <Bell size={18} />
              <div className="portal-notif-dot" />
            </motion.button>

            <AnimatePresence>
              {showNotifications && (
                <motion.div
                  initial={{ opacity: 0, y: 10, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 10, scale: 0.95 }}
                  transition={{ duration: 0.15 }}
                  className="portal-dropdown-menu"
                  style={{ right: 0, top: 'calc(100% + 8px)', width: '300px' }}
                >
                  <div className="portal-dropdown-header" style={{ borderBottom: '1px solid #f3f4f6', paddingBottom: '0.5rem', marginBottom: '0.5rem' }}>
                    <h3 style={{ margin: 0, fontSize: '0.875rem', fontWeight: 600, color: '#1f2937' }}>Notifications</h3>
                  </div>
                  <div style={{ maxHeight: '240px', overflowY: 'auto' }}>
                    <div className="portal-notif-item" style={{ padding: '0.5rem 0', display: 'flex', gap: '0.75rem', borderBottom: '1px solid #f9fafb' }}>
                      <div className="portal-notif-icon">📝</div>
                      <div className="portal-notif-content">
                        <p>Please submit your pending exam papers.</p>
                        <span>2 hours ago</span>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <div style={{ position: 'relative' }}>
            <motion.button
              className="portal-user-btn"
              whileHover={{ scale: 1.02 }}
              onClick={() => setShowProfileMenu(!showProfileMenu)}
            >
              {avatarUrl && !imgFailed ? (
                <img
                  src={avatarUrl}
                  alt={fullName}
                  className="portal-avatar"
                  style={{ objectFit: 'cover' }}
                  onError={() => setImgFailed(true)}
                />
              ) : (
                <div className="portal-avatar">{initials}</div>
              )}
              <div className="portal-user-info">
                <span className="portal-user-name">{fullName || username}</span>
                <span className="portal-user-sub">{username}</span>
              </div>
              <motion.div animate={{ rotate: showProfileMenu ? 180 : 0 }} transition={{ duration: 0.2 }}>
                <ChevronDown size={14} className="portal-chevron" />
              </motion.div>
            </motion.button>

            <AnimatePresence>
              {showProfileMenu && (
                <motion.div
                  initial={{ opacity: 0, y: 10, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 10, scale: 0.95 }}
                  transition={{ duration: 0.15 }}
                  className="portal-dropdown-menu"
                  style={{ right: 0, top: 'calc(100% + 8px)', width: '220px' }}
                >
                  <div className="portal-dropdown-header" style={{ paddingBottom: '0.5rem', borderBottom: '1px solid #f3f4f6', marginBottom: '0.5rem' }}>
                    <div className="portal-user-info">
                      <span className="portal-user-name" style={{ fontSize: '0.875rem' }}>{fullName || username}</span>
                      <span className="portal-user-sub">{username}</span>
                    </div>
                  </div>

                  <button className="portal-menu-item" onClick={() => { onTabChange('Profile'); setShowProfileMenu(false); }}>
                    <User size={15} /> My Profile
                  </button>
                  <button className="portal-menu-item" onClick={() => { onTabChange('Settings'); setShowProfileMenu(false); }}>
                    <Settings size={15} /> Settings
                  </button>

                  <div style={{ height: '1px', background: '#f3f4f6', margin: '0.5rem 0' }} />

                  <button
                    className="portal-menu-item text-red"
                    onClick={handleLogout}
                  >
                    <LogOut size={15} /> Sign out
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </nav>

      {/* Slide-over Left Drawer for Mobile & Tablet */}
      <AnimatePresence>
        {drawerOpen && (
          <div className="portal-drawer-overlay" onClick={() => setDrawerOpen(false)}>
            <motion.div 
              className="portal-drawer" 
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: 'tween', ease: 'easeInOut', duration: 0.3 }}
              onClick={e => e.stopPropagation()}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--color-border)', paddingBottom: '1rem' }}>
                <span className="portal-brand-name" style={{ fontSize: '1.25rem' }}>Menu</span>
                <button 
                  onClick={() => setDrawerOpen(false)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-muted-foreground)' }}
                >
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: 1 }}>
                {navItems.map(item => (
                  <button
                    key={item.label}
                    onClick={() => {
                      onTabChange(item.label);
                      setDrawerOpen(false);
                    }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.75rem',
                      width: '100%',
                      padding: '0.75rem 1rem',
                      borderRadius: 'var(--radius-md)',
                      border: 'none',
                      fontSize: '0.9rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      background: activeTab === item.label ? 'var(--color-secondary)' : 'transparent',
                      color: activeTab === item.label ? 'var(--color-primary)' : 'var(--color-muted-foreground)',
                      textAlign: 'left'
                    }}
                  >
                    <item.icon size={18} />
                    {item.label}
                  </button>
                ))}
              </div>

              {/* Drawer Footer / Sign Out */}
              <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: '1rem' }}>
                <button
                  className="portal-menu-item text-red"
                  onClick={handleLogout}
                  style={{ padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', display: 'flex', width: '100%' }}
                >
                  <LogOut size={16} /> Sign out
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Sticky Bottom Navigation for Mobile Primary Actions */}
      <div className="portal-bottom-nav">
        {[
          { label: 'Dashboard', icon: LayoutDashboard },
          { label: 'Submissions', icon: ClipboardList, text: 'Papers' },
          { label: 'Analytics', icon: BarChart3 },
          { label: 'Profile', icon: User }
        ].map(item => {
          const Icon = item.icon;
          const label = item.label as PortalTab;
          const isActive = activeTab === label;
          return (
            <button
              key={label}
              onClick={() => onTabChange(label)}
              className={`portal-bottom-nav-item ${isActive ? 'active' : ''}`}
            >
              <Icon size={20} />
              <span>{item.text || label}</span>
            </button>
          );
        })}
      </div>
    </>
  );
}
