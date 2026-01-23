import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/user.dart';
import '../models/file_analysis.dart';
import 'login_screen.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen>
    with SingleTickerProviderStateMixin {
  final ApiService _apiService = ApiService();
  User? _user;
  bool _isLoading = true;
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadProfile();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadProfile() async {
    try {
      final user = await _apiService.getProfile();
      setState(() {
        _user = user;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to load profile: $e'),
          backgroundColor: const Color(0xFFE53E3E),
          behavior: SnackBarBehavior.floating,
          margin: const EdgeInsets.all(16),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FA),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded, color: Color(0xFF2D3748)),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          'Profile',
          style: TextStyle(
            color: Color(0xFF2D3748),
            fontWeight: FontWeight.w600,
            fontSize: 18,
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.edit_rounded, color: Color(0xFF4A5568)),
            onPressed: _isLoading || _user == null
                ? null
                : () => _showEditProfileDialog(),
          ),
        ],
        bottom: _isLoading || _user == null
            ? PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(
            color: const Color(0xFFE2E8F0),
            height: 1,
          ),
        )
            : PreferredSize(
          preferredSize: const Size.fromHeight(49),
          child: Column(
            children: [
              TabBar(
                controller: _tabController,
                indicatorColor: const Color(0xFF3182CE),
                indicatorWeight: 3,
                labelColor: const Color(0xFF3182CE),
                unselectedLabelColor: const Color(0xFF718096),
                labelStyle: const TextStyle(fontWeight: FontWeight.w600),
                tabs: const [
                  Tab(text: 'Profile'),
                  Tab(text: 'File History'),
                ],
              ),
              Container(
                color: const Color(0xFFE2E8F0),
                height: 1,
              ),
            ],
          ),
        ),
      ),
      body: _isLoading
          ? const Center(
        child: CircularProgressIndicator(
          valueColor:
          AlwaysStoppedAnimation<Color>(Color(0xFF3182CE)),
        ),
      )
          : _user == null
          ? _buildErrorState()
          : TabBarView(
        controller: _tabController,
        children: [
          _buildProfileTab(),
          _buildFileHistoryTab(),
        ],
      ),
    );
  }

  Widget _buildProfileTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          _buildProfileHeader(),
          const SizedBox(height: 16),
          _buildProfileInfo(),
          const SizedBox(height: 16),
          _buildActionButtons(),
        ],
      ),
    );
  }

  Widget _buildFileHistoryTab() {
    return FutureBuilder<List<FileAnalysis>>(
      future: _apiService.getAnalysisHistory(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(
            child: CircularProgressIndicator(
              valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF3182CE)),
            ),
          );
        }
        if (snapshot.hasError) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.error_outline,
                    size: 60, color: const Color(0xFFCBD5E0)),
                const SizedBox(height: 16),
                const Text(
                  'Error loading history',
                  style: TextStyle(color: Color(0xFF718096)),
                ),
              ],
            ),
          );
        }

        final files = snapshot.data ?? [];
        if (files.isEmpty) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.history_rounded,
                    size: 80, color: const Color(0xFFCBD5E0)),
                const SizedBox(height: 16),
                const Text(
                  'No files cleaned yet',
                  style: TextStyle(
                    color: Color(0xFF718096),
                    fontSize: 16,
                  ),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Start cleaning files to see your history',
                  style: TextStyle(
                    color: Color(0xFFA0AEC0),
                    fontSize: 14,
                  ),
                ),
              ],
            ),
          );
        }

        return ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: files.length,
          itemBuilder: (context, index) {
            final file = files[index];
            return _buildFileHistoryCard(file);
          },
        );
      },
    );
  }

  Widget _buildFileHistoryCard(FileAnalysis file) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFE2E8F0), width: 1),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () => _showFileComparisonDialog(file),
          borderRadius: BorderRadius.circular(12),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: _getRiskColor(file.riskScore).withOpacity(0.1),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Icon(
                        _getFileIcon(file.fileType),
                        color: _getRiskColor(file.riskScore),
                        size: 24,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            file.filename,
                            style: const TextStyle(
                              color: Color(0xFF2D3748),
                              fontSize: 15,
                              fontWeight: FontWeight.w600,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          const SizedBox(height: 4),
                          Text(
                            file.fileSizeFormatted,
                            style: const TextStyle(
                              color: Color(0xFF718096),
                              fontSize: 13,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const Icon(
                      Icons.arrow_forward_ios_rounded,
                      color: Color(0xFF718096),
                      size: 16,
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0xFFF7FAFC),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Row(
                    children: [
                      Expanded(
                        child: Column(
                          children: [
                            Icon(
                              Icons.warning_rounded,
                              color: _getRiskColor(file.riskScore),
                              size: 28,
                            ),
                            const SizedBox(height: 6),
                            const Text(
                              'Before',
                              style: TextStyle(
                                color: Color(0xFF718096),
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            const SizedBox(height: 6),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 10, vertical: 4),
                              decoration: BoxDecoration(
                                color: _getRiskColor(file.riskScore)
                                    .withOpacity(0.1),
                                borderRadius: BorderRadius.circular(6),
                                border: Border.all(
                                  color: _getRiskColor(file.riskScore)
                                      .withOpacity(0.3),
                                ),
                              ),
                              child: Text(
                                '${file.metadataCount}',
                                style: TextStyle(
                                  color: _getRiskColor(file.riskScore),
                                  fontSize: 11,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const Padding(
                        padding: EdgeInsets.symmetric(horizontal: 8),
                        child: Icon(
                          Icons.arrow_forward_rounded,
                          color: Color(0xFFCBD5E0),
                          size: 20,
                        ),
                      ),
                      Expanded(
                        child: Column(
                          children: [
                            const Icon(
                              Icons.verified_rounded,
                              color: Color(0xFF38A169),
                              size: 28,
                            ),
                            const SizedBox(height: 6),
                            const Text(
                              'After',
                              style: TextStyle(
                                color: Color(0xFF718096),
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            const SizedBox(height: 6),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 10, vertical: 4),
                              decoration: BoxDecoration(
                                color: const Color(0xFF38A169).withOpacity(0.1),
                                borderRadius: BorderRadius.circular(6),
                                border: Border.all(
                                  color:
                                  const Color(0xFF38A169).withOpacity(0.3),
                                ),
                              ),
                              child: const Text(
                                '0',
                                style: TextStyle(
                                  color: Color(0xFF38A169),
                                  fontSize: 11,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildErrorState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.error_outline_rounded,
            size: 80,
            color: const Color(0xFFCBD5E0),
          ),
          const SizedBox(height: 16),
          const Text(
            'Failed to load profile',
            style: TextStyle(
              color: Color(0xFF718096),
              fontSize: 16,
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: _loadProfile,
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF3182CE),
              padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 14),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
              ),
            ),
            child: const Text('Retry'),
          ),
        ],
      ),
    );
  }

  Widget _buildProfileHeader() {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: const Color(0xFF3182CE),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        children: [
          Container(
            width: 90,
            height: 90,
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.2),
              shape: BoxShape.circle,
            ),
            child: Center(
              child: Text(
                _user!.initials,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 36,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          ),
          const SizedBox(height: 16),
          Text(
            _user!.displayName,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 22,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            '@${_user!.username}',
            style: TextStyle(
              color: Colors.white.withOpacity(0.9),
              fontSize: 15,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildProfileInfo() {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFE2E8F0), width: 1),
      ),
      child: Column(
        children: [
          _buildInfoTile(
            icon: Icons.email_rounded,
            label: 'Email',
            value: _user!.email,
          ),
          Divider(color: const Color(0xFFE2E8F0), height: 1),
          _buildInfoTile(
            icon: Icons.person_rounded,
            label: 'Username',
            value: _user!.username,
          ),
          if (_user!.firstName != null) ...[
            Divider(color: const Color(0xFFE2E8F0), height: 1),
            _buildInfoTile(
              icon: Icons.badge_rounded,
              label: 'First Name',
              value: _user!.firstName!,
            ),
          ],
          if (_user!.lastName != null) ...[
            Divider(color: const Color(0xFFE2E8F0), height: 1),
            _buildInfoTile(
              icon: Icons.badge_rounded,
              label: 'Last Name',
              value: _user!.lastName!,
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildInfoTile({
    required IconData icon,
    required String label,
    required String value,
  }) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: const Color(0xFFEBF8FF),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: const Color(0xFF3182CE), size: 20),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: const TextStyle(
                    color: Color(0xFF718096),
                    fontSize: 12,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  value,
                  style: const TextStyle(
                    color: Color(0xFF2D3748),
                    fontSize: 15,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildActionButtons() {
    return Column(
      children: [
        _buildActionButton(
          icon: Icons.lock_reset_rounded,
          label: 'Change Password',
          color: const Color(0xFF3182CE),
          onTap: () => _showChangePasswordDialog(),
        ),
        const SizedBox(height: 10),
        _buildActionButton(
          icon: Icons.logout_rounded,
          label: 'Logout',
          color: const Color(0xFFED8936),
          onTap: () => _showLogoutDialog(),
        ),
        const SizedBox(height: 10),
        _buildActionButton(
          icon: Icons.delete_forever_rounded,
          label: 'Delete Account',
          color: const Color(0xFFE53E3E),
          onTap: () => _showDeleteAccountDialog(),
        ),
      ],
    );
  }

  Widget _buildActionButton({
    required IconData icon,
    required String label,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: color.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(icon, color: color, size: 22),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Text(
                    label,
                    style: const TextStyle(
                      color: Color(0xFF2D3748),
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                const Icon(
                  Icons.chevron_right_rounded,
                  color: Color(0xFF718096),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  // Helper methods
  IconData _getFileIcon(String fileType) {
    if (fileType.contains('image')) return Icons.image_rounded;
    if (fileType.contains('pdf')) return Icons.picture_as_pdf_rounded;
    if (fileType.contains('document')) return Icons.description_rounded;
    return Icons.insert_drive_file_rounded;
  }

  IconData _getCategoryIcon(String category) {
    switch (category.toLowerCase()) {
      case 'location':
        return Icons.location_on_rounded;
      case 'device':
        return Icons.phone_android_rounded;
      case 'software':
        return Icons.computer_rounded;
      case 'camera':
        return Icons.camera_alt_rounded;
      case 'personal':
        return Icons.person_rounded;
      case 'temporal':
        return Icons.access_time_rounded;
      default:
        return Icons.info_rounded;
    }
  }

  Color _getRiskColor(int riskScore) {
    if (riskScore >= 80) return const Color(0xFFE53E3E);
    if (riskScore >= 60) return const Color(0xFFED8936);
    if (riskScore >= 40) return const Color(0xFFECC94B);
    return const Color(0xFF38A169);
  }

  Color _getRiskColorForLevel(String level) {
    switch (level.toLowerCase()) {
      case 'critical':
        return const Color(0xFFE53E3E);
      case 'high':
        return const Color(0xFFED8936);
      case 'medium':
        return const Color(0xFFECC94B);
      default:
        return const Color(0xFF38A169);
    }
  }

  void _showFileComparisonDialog(FileAnalysis file) {
    showDialog(
      context: context,
      builder: (context) => Dialog(
        backgroundColor: Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        child: Container(
          constraints: const BoxConstraints(maxWidth: 500),
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Text(
                        file.filename,
                        style: const TextStyle(
                          color: Color(0xFF2D3748),
                          fontSize: 18,
                          fontWeight: FontWeight.w700,
                        ),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.close, color: Color(0xFF718096)),
                      onPressed: () => Navigator.pop(context),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                Text(
                  'BEFORE CLEANING',
                  style: TextStyle(
                    color: const Color(0xFF718096),
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.2,
                  ),
                ),
                const SizedBox(height: 10),
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: _getRiskColor(file.riskScore).withOpacity(0.05),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: _getRiskColor(file.riskScore).withOpacity(0.2),
                    ),
                  ),
                  child: Column(
                    children: [
                      _buildComparisonRow('Risk Score',
                          '${file.riskScore}/100', _getRiskColor(file.riskScore)),
                      const SizedBox(height: 10),
                      _buildComparisonRow(
                          'Metadata Found', '${file.metadataCount} entries', null),
                      const SizedBox(height: 10),
                      _buildComparisonRow('Risk Level', file.riskLevel,
                          _getRiskColor(file.riskScore)),
                    ],
                  ),
                ),
                const SizedBox(height: 20),
                Text(
                  'AFTER CLEANING',
                  style: TextStyle(
                    color: const Color(0xFF718096),
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.2,
                  ),
                ),
                const SizedBox(height: 10),
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: const Color(0xFF38A169).withOpacity(0.05),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: const Color(0xFF38A169).withOpacity(0.2),
                    ),
                  ),
                  child: Column(
                    children: [
                      _buildComparisonRow(
                          'Risk Score', '0/100', const Color(0xFF38A169)),
                      const SizedBox(height: 10),
                      _buildComparisonRow('Metadata Found', '0 entries', null),
                      const SizedBox(height: 10),
                      _buildComparisonRow(
                          'Risk Level', 'Safe', const Color(0xFF38A169)),
                    ],
                  ),
                ),
                const SizedBox(height: 20),
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: const Color(0xFF3182CE),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.check_circle_rounded,
                          color: Colors.white, size: 22),
                      const SizedBox(width: 10),
                      Text(
                        '${file.metadataCount} entries removed',
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w600,
                          fontSize: 15,
                        ),
                      ),
                    ],
                  ),
                ),
                if (file.metadataEntries.isNotEmpty) ...[
                  const SizedBox(height: 20),
                  Text(
                    'REMOVED METADATA',
                    style: TextStyle(
                      color: const Color(0xFF718096),
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.2,
                    ),
                  ),
                  const SizedBox(height: 10),
                  ...file.metadataEntries.take(5).map((entry) => Container(
                    margin: const EdgeInsets.only(bottom: 8),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: const Color(0xFFF7FAFC),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          _getCategoryIcon(entry.category),
                          color: _getRiskColorForLevel(entry.riskLevel),
                          size: 16,
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            entry.key,
                            style: const TextStyle(
                              color: Color(0xFF4A5568),
                              fontSize: 13,
                            ),
                          ),
                        ),
                      ],
                    ),
                  )),
                  if (file.metadataEntries.length > 5)
                    Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: Text(
                        '+${file.metadataEntries.length - 5} more removed',
                        style: const TextStyle(
                          color: Color(0xFF718096),
                          fontSize: 12,
                          fontStyle: FontStyle.italic,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildComparisonRow(String label, String value, Color? valueColor) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: const TextStyle(
            color: Color(0xFF718096),
            fontSize: 14,
          ),
        ),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
          decoration: BoxDecoration(
            color: valueColor?.withOpacity(0.1) ?? Colors.transparent,
            borderRadius: BorderRadius.circular(6),
            border: valueColor != null
                ? Border.all(color: valueColor.withOpacity(0.3))
                : null,
          ),
          child: Text(
            value,
            style: TextStyle(
              color: valueColor ?? const Color(0xFF2D3748),
              fontWeight: FontWeight.w600,
              fontSize: 14,
            ),
          ),
        ),
      ],
    );
  }

  void _showEditProfileDialog() {
    final firstNameController =
    TextEditingController(text: _user!.firstName ?? '');
    final lastNameController =
    TextEditingController(text: _user!.lastName ?? '');
    final emailController = TextEditingController(text: _user!.email);

    showDialog(
      context: context,
      builder: (context) => Dialog(
        backgroundColor: Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Edit Profile',
                    style: TextStyle(
                      color: Color(0xFF2D3748),
                      fontSize: 18,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, color: Color(0xFF718096)),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
              const SizedBox(height: 20),
              TextField(
                controller: firstNameController,
                style: const TextStyle(color: Color(0xFF2D3748)),
                decoration: InputDecoration(
                  labelText: 'First Name',
                  labelStyle: const TextStyle(color: Color(0xFF718096)),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: const BorderSide(color: Color(0xFFE2E8F0)),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: const BorderSide(color: Color(0xFF3182CE)),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: lastNameController,
                style: const TextStyle(color: Color(0xFF2D3748)),
                decoration: InputDecoration(
                  labelText: 'Last Name',
                  labelStyle: const TextStyle(color: Color(0xFF718096)),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: const BorderSide(color: Color(0xFFE2E8F0)),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: const BorderSide(color: Color(0xFF3182CE)),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: emailController,
                style: const TextStyle(color: Color(0xFF2D3748)),
                decoration: InputDecoration(
                  labelText: 'Email',
                  labelStyle: const TextStyle(color: Color(0xFF718096)),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: const BorderSide(color: Color(0xFFE2E8F0)),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: const BorderSide(color: Color(0xFF3182CE)),
                  ),
                ),
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () async {
                    try {
                      await _apiService.updateProfile(
                        firstName: firstNameController.text.trim(),
                        lastName: lastNameController.text.trim(),
                        email: emailController.text.trim(),
                      );

                      if (!mounted) return;
                      Navigator.pop(context);

                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content:
                          const Text('Profile updated successfully!'),
                          backgroundColor: const Color(0xFF38A169),
                          behavior: SnackBarBehavior.floating,
                          shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(10)),
                          margin: const EdgeInsets.all(16),
                        ),
                      );

                      _loadProfile();
                    } catch (e) {
                      if (!mounted) return;
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text('Update failed: $e'),
                          backgroundColor: const Color(0xFFE53E3E),
                          margin: const EdgeInsets.all(16),
                        ),
                      );
                    }
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF3182CE),
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10),
                    ),
                  ),
                  child: const Text(
                    'Save Changes',
                    style: TextStyle(
                      fontWeight: FontWeight.w600,
                      fontSize: 16,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showChangePasswordDialog() {
    final oldPasswordController = TextEditingController();
    final newPasswordController = TextEditingController();
    final confirmPasswordController = TextEditingController();

    showDialog(
      context: context,
      builder: (context) => Dialog(
        backgroundColor: Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Change Password',
                    style: TextStyle(
                      color: Color(0xFF2D3748),
                      fontSize: 18,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, color: Color(0xFF718096)),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
              const SizedBox(height: 20),
              TextField(
                controller: oldPasswordController,
                obscureText: true,
                style: const TextStyle(color: Color(0xFF2D3748)),
                decoration: InputDecoration(
                  labelText: 'Current Password',
                  labelStyle: const TextStyle(color: Color(0xFF718096)),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: const BorderSide(color: Color(0xFFE2E8F0)),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: const BorderSide(color: Color(0xFF3182CE)),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: newPasswordController,
                obscureText: true,
                style: const TextStyle(color: Color(0xFF2D3748)),
                decoration: InputDecoration(
                  labelText: 'New Password',
                  labelStyle: const TextStyle(color: Color(0xFF718096)),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: const BorderSide(color: Color(0xFFE2E8F0)),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: const BorderSide(color: Color(0xFF3182CE)),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: confirmPasswordController,
                obscureText: true,
                style: const TextStyle(color: Color(0xFF2D3748)),
                decoration: InputDecoration(
                  labelText: 'Confirm New Password',
                  labelStyle: const TextStyle(color: Color(0xFF718096)),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: const BorderSide(color: Color(0xFFE2E8F0)),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: const BorderSide(color: Color(0xFF3182CE)),
                  ),
                ),
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () async {
                    if (newPasswordController.text !=
                        confirmPasswordController.text) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('Passwords do not match'),
                          backgroundColor: Color(0xFFE53E3E),
                        ),
                      );
                      return;
                    }

                    try {
                      await _apiService.changePassword(
                        oldPassword: oldPasswordController.text,
                        newPassword: newPasswordController.text,
                        newPassword2: confirmPasswordController.text,
                      );

                      if (!mounted) return;
                      Navigator.pop(context);

                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content:
                          const Text('Password changed successfully!'),
                          backgroundColor: const Color(0xFF38A169),
                          behavior: SnackBarBehavior.floating,
                          shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(10)),
                          margin: const EdgeInsets.all(16),
                        ),
                      );
                    } catch (e) {
                      if (!mounted) return;
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text('Change failed: $e'),
                          backgroundColor: const Color(0xFFE53E3E),
                          margin: const EdgeInsets.all(16),
                        ),
                      );
                    }
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF3182CE),
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10),
                    ),
                  ),
                  child: const Text(
                    'Change Password',
                    style: TextStyle(
                      fontWeight: FontWeight.w600,
                      fontSize: 16,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showLogoutDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text(
          'Logout',
          style: TextStyle(
              color: Color(0xFF2D3748), fontWeight: FontWeight.w700),
        ),
        content: const Text(
          'Are you sure you want to logout?',
          style: TextStyle(color: Color(0xFF718096)),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text(
              'Cancel',
              style: TextStyle(color: Color(0xFF718096)),
            ),
          ),
          TextButton(
            onPressed: () async {
              await _apiService.logout();
              if (!mounted) return;
              Navigator.pushAndRemoveUntil(
                context,
                MaterialPageRoute(builder: (context) => const LoginScreen()),
                    (route) => false,
              );
            },
            child: const Text(
              'Logout',
              style: TextStyle(
                  color: Color(0xFFED8936), fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }

  void _showDeleteAccountDialog() {
    final passwordController = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text(
          'Delete Account',
          style: TextStyle(
              color: Color(0xFFE53E3E), fontWeight: FontWeight.w700),
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'This action cannot be undone. All your data will be permanently deleted.',
              style: TextStyle(color: Color(0xFF718096)),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: passwordController,
              obscureText: true,
              style: const TextStyle(color: Color(0xFF2D3748)),
              decoration: InputDecoration(
                labelText: 'Enter your password to confirm',
                labelStyle: const TextStyle(color: Color(0xFF718096)),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                  borderSide: const BorderSide(color: Color(0xFFE2E8F0)),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                  borderSide: const BorderSide(color: Color(0xFFE53E3E)),
                ),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text(
              'Cancel',
              style: TextStyle(color: Color(0xFF718096)),
            ),
          ),
          TextButton(
            onPressed: () async {
              try {
                await _apiService.deleteAccount(passwordController.text);
                if (!mounted) return;
                Navigator.pushAndRemoveUntil(
                  context,
                  MaterialPageRoute(
                      builder: (context) => const LoginScreen()),
                      (route) => false,
                );
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: const Text('Account deleted successfully'),
                    backgroundColor: const Color(0xFF38A169),
                    margin: const EdgeInsets.all(16),
                  ),
                );
              } catch (e) {
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('Delete failed: $e'),
                    backgroundColor: const Color(0xFFE53E3E),
                    margin: const EdgeInsets.all(16),
                  ),
                );
              }
            },
            child: const Text(
              'Delete',
              style: TextStyle(
                  color: Color(0xFFE53E3E), fontWeight: FontWeight.w700),
            ),
          ),
        ],
      ),
    );
  }
}