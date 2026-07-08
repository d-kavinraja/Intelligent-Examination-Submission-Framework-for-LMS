import React from 'react';
import { Globe, Mail, Phone, MapPin } from 'lucide-react';
import { motion } from 'framer-motion';

export function PortalFooter() {
  return (
    <footer className="portal-footer" style={{ 
      background: 'white',
      borderTop: '1px solid rgba(226, 232, 240, 0.8)',
      padding: '3rem 0 1.5rem',
      marginTop: '3rem',
      width: '100%',
    }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 1.5rem' }}>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '2.5rem',
          marginBottom: '3rem'
        }}>
          {/* Logo & Description */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '1.25rem', gap: '0.75rem', flexWrap: 'wrap' }}>
              <img 
                src="https://saveetha.ac.in/wp-content/uploads/2024/03/sec-logo-01as.png"
                alt="Saveetha Logo" 
                style={{ height: '48px' }} 
              />
              <div style={{
                background: '#1e3a8a',
                color: '#ffffff',
                padding: '0.2rem 0.5rem',
                borderRadius: '6px',
                fontSize: '0.75rem',
                fontWeight: 700,
                letterSpacing: '0.02em',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                lineHeight: 1.1,
                boxShadow: '0 2px 4px rgba(30, 58, 138, 0.2)'
              }}>
                <span style={{ fontSize: '0.5rem', opacity: 0.8, textTransform: 'uppercase', fontWeight: 600 }}>TNEA Code</span>
                <span>1216</span>
              </div>
            </div>
            <p style={{ color: '#64748b', fontSize: '0.85rem', lineHeight: 1.6, marginBottom: '1.25rem' }}>
              Leading institution dedicated to excellence in technical education and innovation.
            </p>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              {[
                { 
                  label: 'Facebook', 
                  href: 'https://facebook.com',
                  svg: (
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/>
                    </svg>
                  )
                },
                { 
                  label: 'Instagram', 
                  href: 'https://instagram.com',
                  svg: (
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="2" y="2" width="20" height="20" rx="5" ry="5"/>
                      <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/>
                      <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/>
                    </svg>
                  )
                },
                { 
                  label: 'LinkedIn', 
                  href: 'https://linkedin.com',
                  svg: (
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/>
                      <rect x="2" y="9" width="4" height="12"/>
                      <circle cx="4" cy="4" r="2"/>
                    </svg>
                  )
                },
                { 
                  label: 'YouTube', 
                  href: 'https://youtube.com',
                  svg: (
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M22.54 6.42a2.78 2.78 0 0 0-1.94-2C18.88 4 12 4 12 4s-6.88 0-8.6.46a2.78 2.78 0 0 0-1.94 2A29 29 0 0 0 1 11.75a29 29 0 0 0 .46 5.33A2.78 2.78 0 0 0 3.4 19c1.72.46 8.6.46 8.6.46s6.88 0 8.6-.46a2.78 2.78 0 0 0 1.94-2 29 29 0 0 0 .46-5.25 29 29 0 0 0-.46-5.33z"/>
                      <polygon points="9.75 15.02 15.5 11.75 9.75 8.48 9.75 15.02"/>
                    </svg>
                  )
                }
              ].map(social => (
                <motion.a 
                  key={social.label}
                  href={social.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label={social.label}
                  whileHover={{ y: -2, background: '#4f46e5', color: 'white', borderColor: '#4f46e5' }}
                  style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    width: '36px', height: '36px', borderRadius: '8px',
                    background: '#f8fafc', color: '#64748b',
                    border: '1px solid rgba(226, 232, 240, 0.8)',
                    transition: 'all 0.2s ease',
                    textDecoration: 'none'
                  }}
                >
                  {social.svg}
                </motion.a>
              ))}
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h5 style={{ color: '#1e293b', fontSize: '0.95rem', fontWeight: 700, marginBottom: '1.25rem' }}>Quick Links</h5>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {['About College', 'Admissions', 'Departments', 'Research', 'Placements'].map(link => (
                <a key={link} href="#" style={{ color: '#64748b', fontSize: '0.85rem', textDecoration: 'none', transition: 'color 0.2s' }}
                   onMouseOver={e => e.currentTarget.style.color = '#4f46e5'}
                   onMouseOut={e => e.currentTarget.style.color = '#64748b'}>
                  {link}
                </a>
              ))}
            </div>
          </div>

          {/* Resources */}
          <div>
            <h5 style={{ color: '#1e293b', fontSize: '0.95rem', fontWeight: 700, marginBottom: '1.25rem' }}>Resources</h5>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {['Library', 'E-Learning', 'Student Portal', 'Faculty Portal', 'Contact'].map(link => (
                <a key={link} href="#" style={{ color: '#64748b', fontSize: '0.85rem', textDecoration: 'none', transition: 'color 0.2s' }}
                   onMouseOver={e => e.currentTarget.style.color = '#4f46e5'}
                   onMouseOut={e => e.currentTarget.style.color = '#64748b'}>
                  {link}
                </a>
              ))}
            </div>
          </div>

          {/* Contact Info */}
          <div>
            <h5 style={{ color: '#1e293b', fontSize: '0.95rem', fontWeight: 700, marginBottom: '1.25rem' }}>Contact Info</h5>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', color: '#64748b', fontSize: '0.85rem', lineHeight: 1.5 }}>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
                <MapPin size={16} style={{ color: '#4f46e5', marginTop: '2px', flexShrink: 0 }} />
                <span>Thandalam, Chennai - 602105<br />Tamil Nadu, India</span>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <Phone size={16} style={{ color: '#4f46e5', flexShrink: 0 }} />
                <span>+91 44 6681 1000</span>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <Mail size={16} style={{ color: '#4f46e5', flexShrink: 0 }} />
                <span>info@saveetha.ac.in</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Bottom */}
        <div style={{ 
          borderTop: '1px solid rgba(226, 232, 240, 0.8)', 
          paddingTop: '1.5rem', 
          textAlign: 'center' 
        }}>
          <p style={{ color: '#64748b', fontSize: '0.8rem', margin: '0 0 0.5rem' }}>
            © {new Date().getFullYear()} Saveetha Engineering College. All rights reserved. | <a href="#" style={{ color: '#64748b', textDecoration: 'none' }}>Privacy Policy</a> | <a href="#" style={{ color: '#64748b', textDecoration: 'none' }}>Terms of Service</a>
          </p>
          <p style={{ color: '#94a3b8', fontSize: '0.75rem', margin: 0 }}>
            Examination Middleware System - Department of Artificial Intelligence and Machine Learning
          </p>
        </div>
      </div>
    </footer>
  );
}
