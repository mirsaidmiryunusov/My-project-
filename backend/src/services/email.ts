/**
 * Email Service
 * 
 * Email sending service for notifications, password resets, and other communications.
 */

import { logger } from '../utils/logger';

export class EmailService {
  private isConfigured: boolean;

  constructor() {
    // Check if email service is configured
    this.isConfigured = !!(
      process.env.SMTP_HOST &&
      process.env.SMTP_PORT &&
      process.env.SMTP_USER &&
      process.env.SMTP_PASS
    );

    if (!this.isConfigured) {
      logger.warn('Email service not configured - emails will be logged instead of sent');
    }
  }

  /**
   * Send password reset email
   */
  async sendPasswordResetEmail(email: string, resetToken: string): Promise<void> {
    try {
      const resetUrl = `${process.env.FRONTEND_URL}/reset-password?token=${resetToken}`;
      
      const emailContent = {
        to: email,
        subject: 'Password Reset - GeminiVoiceConnect',
        html: this.getPasswordResetTemplate(resetUrl),
        text: `Reset your password by visiting: ${resetUrl}`,
      };

      await this.sendEmail(emailContent);
      logger.info(`Password reset email sent to: ${email}`);
    } catch (error) {
      logger.error('Failed to send password reset email:', error);
      throw error;
    }
  }

  /**
   * Send email verification email
   */
  async sendVerificationEmail(email: string, verificationToken: string): Promise<void> {
    try {
      const verificationUrl = `${process.env.FRONTEND_URL}/verify-email?token=${verificationToken}`;
      
      const emailContent = {
        to: email,
        subject: 'Verify Your Email - GeminiVoiceConnect',
        html: this.getVerificationTemplate(verificationUrl),
        text: `Verify your email by visiting: ${verificationUrl}`,
      };

      await this.sendEmail(emailContent);
      logger.info(`Verification email sent to: ${email}`);
    } catch (error) {
      logger.error('Failed to send verification email:', error);
      throw error;
    }
  }

  /**
   * Send welcome email
   */
  async sendWelcomeEmail(email: string, name: string): Promise<void> {
    try {
      const emailContent = {
        to: email,
        subject: 'Welcome to GeminiVoiceConnect',
        html: this.getWelcomeTemplate(name),
        text: `Welcome to GeminiVoiceConnect, ${name}! We're excited to have you on board.`,
      };

      await this.sendEmail(emailContent);
      logger.info(`Welcome email sent to: ${email}`);
    } catch (error) {
      logger.error('Failed to send welcome email:', error);
      throw error;
    }
  }

  /**
   * Send notification email
   */
  async sendNotificationEmail(
    email: string,
    subject: string,
    message: string,
    type: 'info' | 'warning' | 'error' = 'info'
  ): Promise<void> {
    try {
      const emailContent = {
        to: email,
        subject: `${subject} - GeminiVoiceConnect`,
        html: this.getNotificationTemplate(subject, message, type),
        text: message,
      };

      await this.sendEmail(emailContent);
      logger.info(`Notification email sent to: ${email}`);
    } catch (error) {
      logger.error('Failed to send notification email:', error);
      throw error;
    }
  }

  /**
   * Send bulk emails
   */
  async sendBulkEmails(emails: Array<{
    to: string;
    subject: string;
    html: string;
    text: string;
  }>): Promise<void> {
    try {
      const promises = emails.map(email => this.sendEmail(email));
      await Promise.all(promises);
      logger.info(`Bulk emails sent: ${emails.length} emails`);
    } catch (error) {
      logger.error('Failed to send bulk emails:', error);
      throw error;
    }
  }

  /**
   * Core email sending method
   */
  private async sendEmail(emailContent: {
    to: string;
    subject: string;
    html: string;
    text: string;
  }): Promise<void> {
    if (!this.isConfigured) {
      // Log email instead of sending in development/demo mode
      logger.info('Email would be sent:', {
        to: emailContent.to,
        subject: emailContent.subject,
        preview: emailContent.text.substring(0, 100) + '...',
      });
      return;
    }

    // In a real implementation, you would use a service like:
    // - Nodemailer with SMTP
    // - SendGrid
    // - AWS SES
    // - Mailgun
    // etc.

    try {
      // Mock email sending for demo
      await new Promise(resolve => setTimeout(resolve, 100));
      
      logger.info('Email sent successfully:', {
        to: emailContent.to,
        subject: emailContent.subject,
      });
    } catch (error) {
      logger.error('Email sending failed:', error);
      throw new Error('Failed to send email');
    }
  }

  /**
   * Password reset email template
   */
  private getPasswordResetTemplate(resetUrl: string): string {
    return `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <title>Password Reset</title>
        <style>
          body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
          .container { max-width: 600px; margin: 0 auto; padding: 20px; }
          .header { background: #4A90E2; color: white; padding: 20px; text-align: center; }
          .content { padding: 20px; background: #f9f9f9; }
          .button { display: inline-block; padding: 12px 24px; background: #4A90E2; color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }
          .footer { padding: 20px; text-align: center; color: #666; font-size: 12px; }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>GeminiVoiceConnect</h1>
          </div>
          <div class="content">
            <h2>Password Reset Request</h2>
            <p>You have requested to reset your password. Click the button below to create a new password:</p>
            <a href="${resetUrl}" class="button">Reset Password</a>
            <p>If you didn't request this password reset, please ignore this email.</p>
            <p>This link will expire in 24 hours for security reasons.</p>
          </div>
          <div class="footer">
            <p>&copy; 2024 GeminiVoiceConnect. All rights reserved.</p>
          </div>
        </div>
      </body>
      </html>
    `;
  }

  /**
   * Email verification template
   */
  private getVerificationTemplate(verificationUrl: string): string {
    return `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <title>Verify Your Email</title>
        <style>
          body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
          .container { max-width: 600px; margin: 0 auto; padding: 20px; }
          .header { background: #4A90E2; color: white; padding: 20px; text-align: center; }
          .content { padding: 20px; background: #f9f9f9; }
          .button { display: inline-block; padding: 12px 24px; background: #4A90E2; color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }
          .footer { padding: 20px; text-align: center; color: #666; font-size: 12px; }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>GeminiVoiceConnect</h1>
          </div>
          <div class="content">
            <h2>Verify Your Email Address</h2>
            <p>Thank you for signing up! Please verify your email address by clicking the button below:</p>
            <a href="${verificationUrl}" class="button">Verify Email</a>
            <p>If you didn't create an account, please ignore this email.</p>
          </div>
          <div class="footer">
            <p>&copy; 2024 GeminiVoiceConnect. All rights reserved.</p>
          </div>
        </div>
      </body>
      </html>
    `;
  }

  /**
   * Welcome email template
   */
  private getWelcomeTemplate(name: string): string {
    return `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <title>Welcome to GeminiVoiceConnect</title>
        <style>
          body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
          .container { max-width: 600px; margin: 0 auto; padding: 20px; }
          .header { background: #4A90E2; color: white; padding: 20px; text-align: center; }
          .content { padding: 20px; background: #f9f9f9; }
          .button { display: inline-block; padding: 12px 24px; background: #4A90E2; color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }
          .footer { padding: 20px; text-align: center; color: #666; font-size: 12px; }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>Welcome to GeminiVoiceConnect!</h1>
          </div>
          <div class="content">
            <h2>Hello ${name}!</h2>
            <p>Welcome to GeminiVoiceConnect, the AI-powered call center management platform.</p>
            <p>You now have access to:</p>
            <ul>
              <li>Real-time call monitoring and analytics</li>
              <li>AI-powered predictions and insights</li>
              <li>Advanced customer management</li>
              <li>Comprehensive reporting tools</li>
            </ul>
            <a href="${process.env.FRONTEND_URL}/dashboard" class="button">Get Started</a>
            <p>If you have any questions, our support team is here to help!</p>
          </div>
          <div class="footer">
            <p>&copy; 2024 GeminiVoiceConnect. All rights reserved.</p>
          </div>
        </div>
      </body>
      </html>
    `;
  }

  /**
   * Notification email template
   */
  private getNotificationTemplate(
    subject: string,
    message: string,
    type: 'info' | 'warning' | 'error'
  ): string {
    const colors = {
      info: '#4A90E2',
      warning: '#F5A623',
      error: '#D0021B',
    };

    return `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <title>${subject}</title>
        <style>
          body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
          .container { max-width: 600px; margin: 0 auto; padding: 20px; }
          .header { background: ${colors[type]}; color: white; padding: 20px; text-align: center; }
          .content { padding: 20px; background: #f9f9f9; }
          .footer { padding: 20px; text-align: center; color: #666; font-size: 12px; }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>GeminiVoiceConnect</h1>
          </div>
          <div class="content">
            <h2>${subject}</h2>
            <p>${message}</p>
          </div>
          <div class="footer">
            <p>&copy; 2024 GeminiVoiceConnect. All rights reserved.</p>
          </div>
        </div>
      </body>
      </html>
    `;
  }
}